# Gate Release Bundles on Completed Image Builds

## Context

Every release channel publishes a deployment bundle as a GitHub Release asset. The deploy VMs fetch that bundle on their
15-minute `infra-pull` tick and immediately `docker compose pull` the version-pinned tags inside it. Until now the
bundle was published in parallel with the image builds:

- `build-rc.yml` dispatched the seven `build-*.yml` workflows and returned, while `publish-rc-bundle` depended only on
  the tagging job.
- `add-tag.yml` fired the `release-ready` `repository_dispatch` and returned, while `publish-nightly-bundle` depended
  only on the tagging job.
- `promote.yml` waited for the image retag in rc mode, but the hotfix path dispatched the builds and left
  `build-release` gated on npm/PyPI alone.

Whichever image finishes last therefore decides whether a deploy in that window succeeds. On `v0.320.0-rc.1` the bundle
was published at 02:39:44 UTC and `email_classification_agent` finished pushing at 02:41:24; the staging deploy in
between failed with `failed to resolve reference ...: not found`. Every build had succeeded — the bundle was simply
~100 seconds early. The Ansible deploy retries three times at 10-second intervals and then alerts Slack and SigNoz, so
the window produces a spurious failure alert and a stack that only updates on the next tick.

Decision 3.1 of [the component-specific build pipeline ADR](2025_08_11_microservice_build_pipeline_architecture.md)
chose `repository_dispatch` over `workflow_run` for chaining builds. That choice is what makes the nightly race
unfixable in place: a `repository_dispatch` run carries no ref that identifies it, and it runs the workflow on the
default branch rather than at the tagged commit, so the tagging workflow cannot tell which runs are its own and cannot
wait for them.

## Decision Drivers

- *A published bundle must be deployable* — the deploy VMs treat the bundle as the signal that a version is ready.
- *Real failures must stay visible* — a channel that cries wolf every build trains everyone to ignore its alerts.
- *An image must match its tag* — a build triggered on the default branch can pick up a later commit than the one the
  tag points at.
- *One mechanism for all channels* — nightly, rc and hotfix should fail (or not) for the same reasons.

## Decision

Dispatch the per-image build workflows with `workflow_dispatch` **at the release ref**, and block the publishing job
until every dispatched run has completed successfully.

- A composite action, `.github/actions/dispatch_builds`, dispatches the workflows and waits on each run with
  `gh run watch --exit-status`. The release ref is a unique version tag, so `--branch <tag> --event workflow_dispatch`
  identifies a run of this fan-out; run ids seen before the dispatch are recorded so a re-dispatch at an existing tag
  waits for its own run.
- `build-rc.yml` (`publish-rc-bundle`), `add-tag.yml` (`publish-nightly-bundle`) and `promote.yml` (`build-release`, for
  the hotfix path) declare the fan-out job in `needs`.
- The seven `build-*.yml` workflows drop their `repository_dispatch: [release-ready]` trigger and the
  `client_payload` / `event_name == 'repository_dispatch'` branches that only that trigger reached. This supersedes
  Decision 3.1 of the 2025-08-11 ADR **for release image builds**.
- `release-ready` remains as the trigger for `deploy-docs.yml`, which has no ordering constraint and legitimately wants
  the payload version.

## Consequences

### Positive

- A published bundle always has its images in the registry, so a deploy that fails on a missing tag is a real failure.
- Nightly images are now built from the tagged commit instead of whatever `main` pointed at when the build started.
- The three channels share one mechanism, so a fix or a diagnosis applies to all of them.

### Negative

- The bundle now lands roughly as late as the slowest image build (a few minutes) instead of immediately.
- The publishing job's fate is tied to the builds: one failing image blocks the bundle for the whole channel. That is
  the intent, but it makes a flaky build more disruptive than before.
- The wait relies on `gh run watch`, so a workflow whose failure is masked (for example a matrix job with
  `continue-on-error: true`) is still reported as a success to the gate.
