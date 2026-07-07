#!/usr/bin/env bash
#
# Bring up the full EKS deployment as a reproducible runbook:
#   1. cluster (VPC, NAT, managed nodegroup, OIDC)
#   2. AWS Load Balancer Controller (IRSA + Helm)
#   3. EBS CSI driver (for SQLite-on-volume persistence)
#   4. build + push the backend/frontend images to ECR (amd64 — EKS nodes are amd64)
#   5. create the app Secret out-of-band (never in Helm values/history)
#   6. helm upgrade --install, then print the ALB hostname
#
# This is a runbook, not magic: it captures the exact steps used to stand the demo
# up. Review the vars and deploy/eks/values.yaml first. Chart/policy versions drift
# over time — confirm the AWS Load Balancer Controller chart + IAM policy match.
#
# Prereqs: awscli (authenticated), eksctl, kubectl, helm, docker. Override via env:
#   CLUSTER=agui-demo REGION=us-east-1 RELEASE=agui-demo NODES=2 NODE_TYPE=t3.medium \
#   SECRETS_ENV=deploy/eks/secrets.env ./deploy/eks/deploy.sh
set -euo pipefail

CLUSTER="${CLUSTER:-agui-demo}"
REGION="${REGION:-us-east-1}"
RELEASE="${RELEASE:-agui-demo}"
NODE_TYPE="${NODE_TYPE:-t3.medium}"
NODES="${NODES:-2}"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
ECR="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SECRETS_ENV="${SECRETS_ENV:-$REPO_ROOT/deploy/eks/secrets.env}"
ALB_POLICY_VERSION="${ALB_POLICY_VERSION:-v2.7.0}"

# 1) Cluster --------------------------------------------------------------------
if ! eksctl get cluster --name "$CLUSTER" --region "$REGION" >/dev/null 2>&1; then
  echo ">> Creating cluster '$CLUSTER' ($NODES x $NODE_TYPE) — ~15-20 min"
  eksctl create cluster --name "$CLUSTER" --region "$REGION" \
    --nodegroup-name ng --node-type "$NODE_TYPE" --nodes "$NODES" --with-oidc --managed
else
  echo ">> Cluster '$CLUSTER' already exists; ensuring the OIDC provider"
  eksctl utils associate-iam-oidc-provider --cluster "$CLUSTER" --region "$REGION" --approve
fi

# 2) AWS Load Balancer Controller ----------------------------------------------
echo ">> Installing the AWS Load Balancer Controller"
curl -fsSL -o /tmp/alb-iam-policy.json \
  "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/${ALB_POLICY_VERSION}/docs/install/iam_policy.json"
aws iam create-policy --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file:///tmp/alb-iam-policy.json 2>/dev/null || true
eksctl create iamserviceaccount --cluster "$CLUSTER" --region "$REGION" \
  --namespace kube-system --name aws-load-balancer-controller \
  --attach-policy-arn "arn:aws:iam::${ACCOUNT}:policy/AWSLoadBalancerControllerIAMPolicy" \
  --approve --override-existing-serviceaccounts
helm repo add eks https://aws.github.io/eks-charts >/dev/null 2>&1 || true
helm repo update >/dev/null
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system --set clusterName="$CLUSTER" \
  --set serviceAccount.create=false --set serviceAccount.name=aws-load-balancer-controller

# 3) EBS CSI driver (SQLite-on-volume) -----------------------------------------
echo ">> Installing the EBS CSI driver addon"
eksctl create iamserviceaccount --cluster "$CLUSTER" --region "$REGION" \
  --namespace kube-system --name ebs-csi-controller-sa \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve --override-existing-serviceaccounts --role-only \
  --role-name AmazonEKS_EBS_CSI_DriverRole
eksctl create addon --cluster "$CLUSTER" --region "$REGION" --name aws-ebs-csi-driver \
  --service-account-role-arn "arn:aws:iam::${ACCOUNT}:role/AmazonEKS_EBS_CSI_DriverRole" --force

# 4) Images (EKS nodes are amd64) ----------------------------------------------
echo ">> Building and pushing images to $ECR"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR"
for repo in agui-demo-backend agui-demo-frontend; do
  aws ecr describe-repositories --repository-names "$repo" --region "$REGION" >/dev/null 2>&1 \
    || aws ecr create-repository --repository-name "$repo" --region "$REGION" >/dev/null
done
docker build --platform linux/amd64 -f "$REPO_ROOT/backend/Dockerfile" \
  -t "$ECR/agui-demo-backend:latest" "$REPO_ROOT"
docker build --platform linux/amd64 -f "$REPO_ROOT/frontend/Dockerfile" \
  -t "$ECR/agui-demo-frontend:latest" "$REPO_ROOT/frontend"
docker push "$ECR/agui-demo-backend:latest"
docker push "$ECR/agui-demo-frontend:latest"

# 5) App Secret (out-of-band) ---------------------------------------------------
if [ -f "$SECRETS_ENV" ]; then
  echo ">> Applying the '$RELEASE-secrets' Secret from $SECRETS_ENV"
  kubectl create secret generic "$RELEASE-secrets" --from-env-file="$SECRETS_ENV" \
    --dry-run=client -o yaml | kubectl apply -f -
else
  echo "!! $SECRETS_ENV not found — create it (DATABASE_URL, GEMINI_API_KEY, ...) before deploying"
  exit 1
fi

# 6) Chart ----------------------------------------------------------------------
echo ">> helm upgrade --install $RELEASE"
helm upgrade --install "$RELEASE" "$REPO_ROOT/deploy/eks" \
  -f "$REPO_ROOT/deploy/eks/values.yaml" \
  --set backend.image="$ECR/agui-demo-backend:latest" \
  --set frontend.image="$ECR/agui-demo-frontend:latest"

echo ">> Waiting for the ALB hostname"
ADDR=""
for _ in $(seq 1 30); do
  ADDR=$(kubectl get ingress "$RELEASE" \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
  [ -n "$ADDR" ] && break; sleep 10
done
echo ">> ALB: ${ADDR:-<pending; check 'kubectl get ingress'>}"
echo ">> For custom domains, point the frontend + api CNAMEs at that ALB hostname."
