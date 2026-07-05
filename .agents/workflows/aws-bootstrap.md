---
description: One-time AWS bootstrap — create the scoped deployer IAM user with root, then switch to it
---

## Steps

### 1. Preconditions (root, one time only)
- The `aws` CLI is installed and root/admin credentials are configured for this
  one-time step. Confirm: `aws sts get-caller-identity`.

### 2. Create the scoped deployer user
- Run `bash deploy/aws/bootstrap_iam.sh`. It creates the `agui-deployer` IAM
  user, attaches `deploy/aws/iam-policy.json` (ECR `agui-demo-*`, Bedrock
  AgentCore, EKS access), and prints access keys.

### 3. Switch to the deployer profile
- `aws configure --profile agui-deployer` (paste the printed keys), then verify
  `aws sts get-caller-identity --profile agui-deployer`.

### 4. Never use root again
- Use `--profile agui-deployer` (or `AWS_PROFILE=agui-deployer`) for every AWS
  command from now on. Then follow `deploy/agentcore/README.md` and
  `deploy/eks/README.md`.

Never commit access keys. See `deploy/aws/README.md`.
