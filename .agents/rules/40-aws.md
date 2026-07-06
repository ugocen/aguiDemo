# AWS: scoped deployer preferred, root authorized by the owner when needed

- Prefer the scoped IAM deployer user, profile `agui-deployer`
  (`--profile agui-deployer` or `AWS_PROFILE=agui-deployer`), for routine work.
- The repo owner has **authorized using the root account** (`default` profile)
  directly when it is needed to acquire permissions or create infrastructure the
  scoped user cannot — e.g. creating the EKS cluster and RDS, `iam:PassRole`, or
  attaching broader policies. The earlier "never use root" restriction is lifted.
- Never put credentials in the repo or in code. Keep AWS keys in the named
  profile in `~/.aws/credentials`; never commit access keys.
- Connecting to AWS is allowed and not restricted by the isolation rule — that
  rule is only about installing packages.

Flow: `/aws-bootstrap` (once) → configure `agui-deployer` profile → follow
`deploy/agentcore/README.md` and `deploy/eks/README.md` with that profile.
