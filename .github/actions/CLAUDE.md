# .github/actions - Reusable GitHub Actions

**Purpose**: Composite GitHub Actions for CI/CD. Consumed by this repo's workflows (`.github/workflows/`) and external
customer repos. Each action is a single `action.yml` file. NOT repository-specific workflows — those consume these
actions.

## Folder Structure

```
.github/actions/
├── build_image/               # Docker image build + push to GHCR
├── lint_backend/              # Python linting (Ruff format via reviewdog)
├── lint_frontend/             # Nuxt linting (ESLint via reviewdog)
├── pytest_coverage_comment/   # PR coverage comment (downloads test_backend artifacts)
├── sonarcloud_scan/           # SonarCloud quality analysis (downloads test_backend artifacts)
└── test_backend/              # Python tests with coverage + artifact upload
```

## Composite Action Rules

- **`shell: bash` required** on every `run:` step. Composite actions do NOT inherit shell from the caller workflow.
  Omitting it causes a hard failure.
- All actions start with `actions/checkout@v4` as their first step
- Git auth: HTTPS token rewrite (`git config --global url."https://$TOKEN@github.com/"...`) or SSH key setup

## Action Coupling (test_backend -> coverage/sonar)

`test_backend` uploads artifacts with names derived from `working_directory`:

- `{working_directory}-coverage-report` (coverage.xml)
- `{working_directory}-pytest-report` (pytest.xml)

Both `pytest_coverage_comment` and `sonarcloud_scan` download artifacts by these **exact names**. Changing the naming
convention in any one action silently breaks the others. Always update all three together.

## Deferred Test Failure (test_backend)

`test_backend` does NOT fail immediately on test failure:

1. Captures pytest exit code into a variable
2. Exit code 5 (no tests found) creates an empty `pytest.xml` — does NOT fail the action
3. Exit code != 0 sets `TEST_FAIL=true` env var
4. Uploads coverage + pytest XML artifacts (always, regardless of test outcome)
5. "Check if Tests Failed" step runs LAST — `exit 1` only after artifacts are uploaded

This ensures downstream jobs (`pytest_coverage_comment`, `sonarcloud_scan`) always receive artifacts even when tests
fail.

## Action Details

**build_image**: Two separate `docker/build-push-action@v6` steps controlled by `if: ${{ inputs.ssh_key != '' }}`. When
`ssh_key` is provided, the build gets SSH access to private repos during Docker build. When empty, a simpler step runs
with the `VERSION` build-arg plus the optional `build_args` input (one `KEY=VALUE` per line; the Presidio analyzer's GPU
image passes its CUDA torch index this way). Tags: `ghcr.io/{owner}/{repo}/{image_name}:{version}` with optional
`secondary_tag` (nightly/latest). `cache_scope` (default empty = no cache) reads and writes the GitHub Actions build
cache under that scope. Release builds and the PR `build-images` job in `analyze-test-pr.yml` use the same scopes
(`agent` for all agent images, `pipeline` for the pipeline apps, the image name otherwise), so they share layers.

**PR target selection**: `.github/scripts/ci_targets.py` decides which modules `analyze-test-pr.yml` tests (and how many
shards each gets) and which images it builds without pushing. A module runs when its folder, a module it depends on, or
a shared input (core, `uv.lock`, root `pyproject.toml`, `infra/`, `Makefile`, `.env.dev`, the test action, the workflow,
the script) changed; pushes to `main` test every module. Every required SonarCloud check still reports, with coverage
only for the modules that were tested.

**lint_backend**: Uses `ruff format` via reviewdog. Aligned with local development (`make pr-ready` also uses
`ruff format`).

**lint_frontend**: Requires `lockfile` input (path to pnpm lockfile) in addition to `working_directory` — used for pnpm
cache key. Runs `nuxi prepare` before linting to generate Nuxt type stubs.

**test_backend**: Most complex action. Key inputs:

- `docker_compose_services`: space-separated list of Docker services to start (empty = no Docker)
- `install_ffmpeg`: installs FFmpeg via `make install-ffmpeg`
- `huggingface_api_key`: added to `.env.dev` for model downloads
- `swiss_llm_cloud_*`: Swiss LLM Cloud secrets (API, embedding, reranking, whisper, OCR) added to `.env.dev`. Only
  `external-tests.yml` passes them; the PR checks run without provider credentials.
- `pytest_markers`: the `-m` expression (default `not flaky`; PR checks pass `not flaky and not external`).
- `shard_index` / `shard_count`: split the module's tests with pytest-split (`least_duration`, timings from the module's
  committed `.test_durations`). Above one shard the job uploads `{working_directory}-shard-{index}` (raw
  `.coverage.shard-N` + `pytest.xml`) instead of the final reports; the `merge-shards` job in `analyze-test-pr.yml`
  combines them and uploads the usual `-coverage-report` / `-pytest-report` artifacts.
- `check_name`: name of the published test-results check (default `working_directory`), so external runs do not
  overwrite the PR check of the same module.
- `regenerate_compose`: runs `make generate-compose` before starting Docker services
- `pytest_timeout_seconds`: per-test budget passed as `--timeout` (default 300). Keep it well under the calling job's
  `timeout-minutes`, otherwise a hung test consumes the whole job and the forced stop discards `pytest.xml`,
  `coverage.xml` and the traceback — the run then reports only "The operation was canceled". `pytest-timeout` comes from
  the workspace root dev group, so every module has it.
- Health check: `docker compose up --wait --wait-timeout 600` fails the job (with `ps` and logs) as soon as a service is
  unhealthy instead of running tests against a broken stack. The runner is discarded afterwards, so there is no teardown
  step.
- Pre-pull login is **best-effort**: the `docker login ghcr.io` in the pre-pull step must not fail the job
  (`|| echo "::warning::..."`). The mirrored images under `ghcr.io/bbvch-ai/aihub-core/*` are public, so an
  expired/absent `PAT_GITHUB_READ_PACKAGES` still lets anonymous pulls succeed. Do NOT make this login fatal again.

**pytest_coverage_comment**: Downloads `{working_directory}-pytest-report` and `{working_directory}-coverage-report`
artifacts from `test_backend`, posts formatted coverage report as PR comment via
`MishaKav/pytest-coverage-comment@main`.

**sonarcloud_scan**: Downloads `{working_directory}-coverage-report` artifact when `report_coverage: true`. Runs
`SonarSource/sonarqube-scan-action@v6`. Requires `sonar_token` and `sonar_project_key` inputs. Default organization:
`bbv-ai`.

## Local vs Remote References

Actions can be referenced two ways:

- **Local** (same checkout): `uses: ./.github/actions/test_backend` — used in `analyze-test-pr.yml` where the action
  needs to run within the same checkout (e.g., `use_local_core: true`)
- **Remote** (cross-job/external): `uses: bbvch-ai/aihub-core/.github/actions/pytest_coverage_comment@main` — used when
  the action runs in a separate job or from external repos

External repos always use remote refs: `uses: bbvch-ai/aihub-core/.github/actions/<action>@main` (or `@v1.0.0` for
pinned versions).

## Caching Layers (test_backend / lint_frontend)

| Cache           | Path                 | Key Strategy                   |
| --------------- | -------------------- | ------------------------------ |
| uv installation | `~/.local`           | `{os}-uv-{version}`            |
| uv cache        | `~/.cache/uv`        | `{os}-uv-cache-{uv.lock hash}` |
| pnpm store      | `$(pnpm store path)` | `{os}-pnpm-{lockfile hash}`    |

## Testing Actions

No unit tests for actions. Changes are tested by:

1. Push to a branch in `swiss-ai-hub`
2. Open PR (triggers `analyze-test-pr.yml`, `lint-pr.yml`) or trigger workflow manually
3. Observe CI results

## Essential Files

- All actions: `.github/actions/*/action.yml`
- Main CI consumer: `.github/workflows/analyze-test-pr.yml` (test + coverage + sonar)
- Build consumer: `.github/workflows/build-agents.yml`
- Lint consumer: `.github/workflows/lint-pr.yml`
