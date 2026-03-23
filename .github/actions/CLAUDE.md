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
with just `VERSION` build-arg. Tags: `ghcr.io/{owner}/{repo}/{image_name}:{version}` with optional `secondary_tag`
(nightly/latest).

**lint_backend**: Uses `ruff format` via reviewdog. Aligned with local development (`make pr-ready` also uses
`ruff format`).

**lint_frontend**: Requires `lockfile` input (path to pnpm lockfile) in addition to `working_directory` — used for pnpm
cache key. Runs `nuxi prepare` before linting to generate Nuxt type stubs.

**test_backend**: Most complex action. Key inputs:

- `docker_compose_services`: space-separated list of Docker services to start (empty = no Docker)
- `install_ffmpeg`: installs FFmpeg via `make install-ffmpeg`
- `huggingface_api_key`: added to `.env.dev` for model downloads
- `swiss_llm_cloud_*`: Swiss LLM Cloud secrets (API, embedding, reranking, whisper, OCR) added to `.env.dev`
- `regenerate_compose`: runs `make generate-compose` before starting Docker services
- Health check polling: waits up to 10 minutes for Docker services to become healthy

**pytest_coverage_comment**: Downloads `{working_directory}-pytest-report` and `{working_directory}-coverage-report`
artifacts from `test_backend`, posts formatted coverage report as PR comment via
`MishaKav/pytest-coverage-comment@main`.

**sonarcloud_scan**: Downloads `{working_directory}-coverage-report` artifact when `report_coverage: true`. Runs
`SonarSource/sonarqube-scan-action@v5`. Requires `sonar_token` and `sonar_project_key` inputs. Default organization:
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
