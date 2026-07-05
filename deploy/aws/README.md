# AWS access — bootstrap once with root, then never use root

**Rule:** the root account is used exactly once, to create a scoped IAM deployer
user. All AWS work after that uses that user (profile `agui-deployer`), never
root.

## One-time bootstrap (root/admin)

```bash
# with root/admin credentials configured
bash deploy/aws/bootstrap_iam.sh
```

This creates the IAM user `agui-deployer`, attaches
[`iam-policy.json`](./iam-policy.json) (scoped to ECR `agui-demo-*`, Bedrock
AgentCore, and EKS access), and prints access keys.

Then configure a named profile and verify:

```bash
aws configure --profile agui-deployer     # paste the printed keys
aws sts get-caller-identity --profile agui-deployer
```

## After bootstrap (always the deployer, never root)

Use `--profile agui-deployer` (or `export AWS_PROFILE=agui-deployer`) for every
AWS command, then follow:

- `deploy/agentcore/README.md` — package and register the agent to Bedrock
  AgentCore (ECR push + AgentCore runtime).
- `deploy/eks/README.md` — deploy the app to EKS with RDS.

## Notes

- Never commit access keys or credentials. `.env` and `*.local` are gitignored;
  keep AWS keys in `~/.aws/credentials` (the named profile), not in the repo.
- The policy is a scoped starting point. Creating a brand-new EKS cluster or RDS
  instance needs broader CloudFormation/EC2/IAM/RDS permissions and is usually a
  one-time admin task; tighten or extend `iam-policy.json` for your account.
