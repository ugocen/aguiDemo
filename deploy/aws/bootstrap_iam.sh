#!/usr/bin/env bash
# One-time AWS bootstrap. Run this ONCE with the root account (or an admin) to
# create a scoped IAM deployer user. After this, use --profile agui-deployer for
# ALL AWS work and never use the root account again.
set -euo pipefail

USER_NAME="${AGUI_DEPLOYER_USER:-agui-deployer}"
POLICY_NAME="${AGUI_DEPLOYER_POLICY:-agui-deployer-policy}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v aws >/dev/null 2>&1 || { echo "aws CLI not found. Install it first."; exit 1; }

echo "This one-time step must run as root/admin. Current caller:"
aws sts get-caller-identity
echo

echo "1) Ensuring IAM user '$USER_NAME' exists..."
aws iam get-user --user-name "$USER_NAME" >/dev/null 2>&1 \
  || aws iam create-user --user-name "$USER_NAME"

echo "2) Ensuring policy '$POLICY_NAME' exists..."
POLICY_ARN="$(aws iam list-policies --scope Local \
  --query "Policies[?PolicyName=='$POLICY_NAME'].Arn | [0]" --output text)"
if [ "$POLICY_ARN" = "None" ] || [ -z "$POLICY_ARN" ]; then
  POLICY_ARN="$(aws iam create-policy --policy-name "$POLICY_NAME" \
    --policy-document "file://$DIR/iam-policy.json" \
    --query 'Policy.Arn' --output text)"
  echo "   created $POLICY_ARN"
else
  echo "   exists $POLICY_ARN (to update: aws iam create-policy-version --policy-arn $POLICY_ARN --policy-document file://$DIR/iam-policy.json --set-as-default)"
fi

echo "3) Attaching policy to user..."
aws iam attach-user-policy --user-name "$USER_NAME" --policy-arn "$POLICY_ARN"

echo "4) Creating access keys (store them securely — shown once):"
aws iam create-access-key --user-name "$USER_NAME"

cat <<EONOTE

Done. Next steps (do NOT use root after this):
  aws configure --profile agui-deployer     # paste the AccessKeyId / SecretAccessKey above
  aws sts get-caller-identity --profile agui-deployer

From now on pass --profile agui-deployer (or export AWS_PROFILE=agui-deployer) to
every AWS command, then follow deploy/agentcore/README.md and deploy/eks/README.md.

Note: this policy scopes ECR (agui-demo-* repos), Bedrock AgentCore, and EKS
access. Creating a new EKS cluster or RDS instance from scratch needs broader
CloudFormation/EC2/IAM/RDS permissions and is typically done once by an admin;
tighten or extend deploy/aws/iam-policy.json for your account.
EONOTE
