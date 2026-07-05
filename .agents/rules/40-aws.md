# AWS: bootstrap once with root, then never use root

- Do all AWS work with the scoped IAM deployer user, profile `agui-deployer`
  (`--profile agui-deployer` or `AWS_PROFILE=agui-deployer`). Never run deploy
  commands as the root account.
- The **only** time the root account is used is the one-time bootstrap
  (`deploy/aws/bootstrap_iam.sh`), which creates that scoped user from
  `deploy/aws/iam-policy.json`. After that, root is never used again.
- Never put credentials in the repo or in code. Keep AWS keys in the named
  profile in `~/.aws/credentials`; never commit access keys.
- Connecting to AWS is allowed and not restricted by the isolation rule — that
  rule is only about installing packages.

Flow: `/aws-bootstrap` (once) → configure `agui-deployer` profile → follow
`deploy/agentcore/README.md` and `deploy/eks/README.md` with that profile.
