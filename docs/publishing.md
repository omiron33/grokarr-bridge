# Publishing (pending Shane's separate approval)

Nothing in this repo requires pushing. Keep the local repo and image private until Shane approves publication. Do not run the following steps merely because this file exists.

After approval:

1. Choose/verify GitHub owner and public repository `grokarr-bridge`; check license attribution and scan the complete tree/history for secrets and private test endpoints. No NAS evidence/config belongs in the public repo.
2. Set the Git remote, push the local main commit, and create the reviewed `v0.1.0` release/tag. Never push private live-test state or dashboard files.
3. Run the Linux/macOS/Windows test workflow and actual Docker multi-arch build/smoke tests (amd64 + arm64). The Mini did not have a Docker daemon during initial development; that local gap remains until executed elsewhere.
4. Review the optional-app version matrix; mocked API contracts alone are not a live integration certification. Check dependency security advisories and pin release dependency versions/image digest. `uv.lock` captures the tested resolution; maintain it on updates.
5. Run manual **Publish image** workflow with `publish=true`. It writes `ghcr.io/<owner>/grokarr-bridge:0.1.0`, SBOM and provenance. Set package visibility public, verify pulls for both architectures and publish an immutable digest. Default workflow input is build-only; PRs never get publishing credentials.
6. Replace `OWNER` in docs and bot install template with the actual owner and digest. Verify the native Git-tag install from a clean Windows/macOS host. PyPI is optional; verify ownership and configure trusted publishing before claiming `pip install grokarr-bridge` works.
7. Validate GrokArr's actual connector UI supports secure bearer credentials and the chosen private network/Cloudflare Access method. Test no-auth denial and the complete first-run script. Do not use chat as a credential transport if connector support is absent.
8. Provide public README, release notes, supported versions and support/security reporting route. No telemetry or external services are required by the bridge.

Local build without publishing:

```sh
docker buildx build --platform linux/amd64,linux/arm64 --output type=oci,dest=grokarr-bridge.oci.tar -t grokarr-bridge:0.1.0 .
```

This is a release preparation checklist, not proof those platform/image/connector checks have happened.
