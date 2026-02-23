# aihub_action - Reusable GitHub Actions

**Purpose**: Modular GitHub Actions for CI/CD workflows. Standardize build, lint, test, coverage, review across customer
repos.

Tech Stack & Paradigms: GitHub Actions composite actions (YAML workflows). actions/checkout@v4 for repo cloning.
actions/setup-python@v5 (Python 3 default). actions/setup-node@v4 for Node.js. astral-sh/setup-uv@v7 (uv).
docker/setup-buildx-action@v3 + docker/build-push-action@v6 for multi-platform images. docker/login-action@v2 for GHCR
auth. reviewdog/action-black@v3 for Black formatter PR comments. pytest with pytest-cov for coverage.
EnricoMi/publish-unit-test-result-action@v2 for test summaries. actions/upload-artifact@v4 for artifacts.
actions/cache@v4 for HuggingFace model caching. Docker Compose for test services. Stateless, parameterized,
version-tagged reusable actions.

## Scope Responsibility

Reusable CI/CD automation. NOT repository-specific workflows (those consume these actions).

## Folder Structure

```
aihub_action/
├── build_image/               # Docker image build + push
│   └── action.yml
├── lint_backend/              # Backend linting (Black formatter)
│   └── action.yml
├── lint_frontend/             # Frontend linting (ESLint)
│   └── action.yml
├── pytest_coverage_comment/   # PR comment with coverage report
│   └── action.yml
├── review_pr/                 # AI-assisted PR review
│   └── action.yml
├── sonarcloud_scan/           # SonarCloud quality analysis
│   └── action.yml
└── test_backend/              # Backend tests with coverage
    └── action.yml
```

## Action Definition Pattern

**Structure**: Each action has `action.yml` with inputs, composite steps.

**Example** (`lint_backend/action.yml`):

```yaml
name: Lint Backend Code
description: Run linter on python backend

inputs:
  github_token:
    description: 'GitHub token for authentication'
    required: true
  working_directory:
    description: 'Working directory for the linter'
    required: true
  python_version:
    description: 'Python version to install'
    required: false
    default: '3.13'

runs:
  using: "composite"
  steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python_version }}

    - name: Configure Git to Use GITHUB_TOKEN
      shell: bash
      run: git config --global url."https://${{ inputs.github_token }}@github.com/".insteadOf "https://github.com/"

    - name: Lint
      uses: reviewdog/action-black@v3
      with:
        github_token: ${{ inputs.github_token }}
        reporter: github-pr-review
        workdir: ${{ inputs.working_directory }}
```

## Usage in other Repos

**Reference action**: `uses: bbvch-ai/aihub-core/aihub_action/<action_name>@<ref>`

**Example workflow** (`.github/workflows/lint.yml`):

```yaml
name: Lint Backend

on:
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Lint Backend Code
        uses: bbvch-ai/aihub-core/aihub_action/lint_backend@main
        with:
          working_directory: "aihub_agent"
```

## Best Practices

- **Single Responsibility**: Each action focused on one task.
- **Versioning**: Use tagged releases (`@v1.0.0`) in production, `@main` for testing.
- **Inputs**: Document all inputs with descriptions, mark required/optional.
- **Secrets**: Pass sensitive data (tokens, keys) via inputs from repository secrets.

## Common Inputs

- **working_directory**: Path to scope (e.g., `aihub_agent`)
- **github_token**: `${{ secrets.GITHUB_TOKEN }}`
- **sonar_token**: `${{ secrets.SONAR_TOKEN }}`
- **coverage_file**: Path to coverage report

## Testing Actions

**Local**: Not directly possible. Test by:

1. Push to branch in `aihub-core`
2. Trigger workflow, observe results

## Essential Files

- All actions: `/home/user/aihub-core/aihub_action/*/action.yml`
- Example: `/home/user/aihub-core/aihub_action/lint_backend/action.yml`
