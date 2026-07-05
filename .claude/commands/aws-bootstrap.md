---
description: One-time AWS bootstrap — create the scoped deployer IAM user with root, then switch to it
---

Set up AWS access the safe way: use root only once to create a scoped IAM user,
then always use that user.

1. Preconditions: the `aws` CLI is installed and root/admin credentials are
   configured for this one-time step. Confirm with `aws sts get-caller-identity`.
2. Run the bootstrap (creates the `agui-deployer` user, attaches
   `deploy/aws/iam-policy.json`, prints access keys):
   `bash deploy/aws/bootstrap_iam.sh`
3. Configure a named profile with the printed keys and verify:
   `aws configure --profile agui-deployer` then
   `aws sts get-caller-identity --profile agui-deployer`.
4. From now on use `--profile agui-deployer` (or `AWS_PROFILE=agui-deployer`) for
   every AWS command. Never use the root account again.
5. Proceed with `deploy/agentcore/README.md` and `deploy/eks/README.md` using
   that profile.

Never commit access keys. See `deploy/aws/README.md`.
