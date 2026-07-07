#!/usr/bin/env bash
#
# Tear down the EKS deployment: uninstall the app (which deletes the ALB), delete
# the optional AgentCore runtime, then delete the cluster (nodes, NAT, VPC, IRSA).
#
# KEEPS the ACM certificate and the ECR repositories on purpose — they are free
# (cert) or cheap (a few cents of image storage), so a later deploy.sh is fast and
# does not re-run certificate/DNS validation. Only the DNS CNAMEs must be repointed
# at the new ALB after a fresh deploy.
#
# Prereqs: awscli (authenticated), eksctl, helm, kubectl. Override via env:
#   CLUSTER=agui-demo REGION=us-east-1 RELEASE=agui-demo \
#   AGENTCORE_RUNTIME_ID=<id> ./deploy/eks/teardown.sh
set -euo pipefail

CLUSTER="${CLUSTER:-agui-demo}"
REGION="${REGION:-us-east-1}"
RELEASE="${RELEASE:-agui-demo}"
AGENTCORE_RUNTIME_ID="${AGENTCORE_RUNTIME_ID:-}"

echo ">> Uninstalling Helm release '$RELEASE' (removes the ingress -> ALB)"
helm uninstall "$RELEASE" -n default || true

echo ">> Waiting for the ALB to be removed by the controller"
for _ in $(seq 1 30); do
  n=$(aws elbv2 describe-load-balancers --region "$REGION" \
        --query "length(LoadBalancers[?contains(LoadBalancerName, 'aguidemo')])" \
        --output text 2>/dev/null || echo 0)
  if [ "$n" = "0" ]; then echo "   ALB gone"; break; fi
  echo "   still $n ALB(s)..."; sleep 10
done

if [ -n "$AGENTCORE_RUNTIME_ID" ]; then
  echo ">> Deleting AgentCore runtime $AGENTCORE_RUNTIME_ID"
  aws bedrock-agentcore-control delete-agent-runtime \
    --agent-runtime-id "$AGENTCORE_RUNTIME_ID" --region "$REGION" || true
fi

echo ">> Deleting the EKS cluster '$CLUSTER' (nodes, NAT, VPC, IRSA) — ~15-20 min"
eksctl delete cluster --name "$CLUSTER" --region "$REGION" \
  --disable-nodegroup-eviction --wait

echo ">> Done. KEPT: ACM certificate and ECR repositories."
echo "   Re-run deploy.sh to bring it back, then repoint the DNS CNAMEs at the new ALB."
