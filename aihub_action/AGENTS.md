# aihub_action - Reusable GitHub Actions

**Purpose**: Modular GitHub Actions for CI/CD workflows. Standardize build, lint, test, coverage, review across customer repos.

## Scope Responsibility

Reusable CI/CD automation. NOT repository-specific workflows (those consume these actions).

## Folder Structure

```
aihub_action/
├── build_image/               # Docker image build + push
│   └── action.yml
├── lint_backend/              # Backend linting (Ruff + MyPy)
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
name: Lint Backend
description: Lints backend Python code using Ruff and MyPy.

inputs:
  working_directory:
    description: Path to the backend code directory.
    required: true

runs:
  using: "composite"
  steps:
    - name: Checkout Repository
      uses: actions/checkout@v4

    - name: Set up Python 3.13
      uses: actions/setup-python@v5
      with:
        python-version: "3.13"

    - name: Install Dependencies
      shell: bash
      run: |
        cd ${{ inputs.working_directory }}
        pip install poetry
        poetry install

    - name: Run Ruff
      shell: bash
      run: |
        cd ${{ inputs.working_directory }}
        poetry run ruff check

    - name: Run MyPy
      shell: bash
      run: |
        cd ${{ inputs.working_directory }}
        poetry run mypy --strict .
```

## Usage in Customer Repos

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

## Available Actions

**build_image**: Builds Docker images, tags, pushes to registry.
**lint_backend**: Ruff + MyPy (Python strict mode).
**lint_frontend**: ESLint (frontend code quality).
**pytest_coverage_comment**: Posts test coverage % to PR as comment.
**review_pr**: AI-powered PR review with suggestions.
**sonarcloud_scan**: Code quality, security, maintainability analysis.
**test_backend**: pytest with coverage report generation.

## Best Practices

**Single Responsibility**: Each action focused on one task.
**Versioning**: Use tagged releases (`@v1.0.0`) in production, `@main` for testing.
**Inputs**: Document all inputs with descriptions, mark required/optional.
**Secrets**: Pass sensitive data (tokens, keys) via inputs from repository secrets.

## Creating New Actions

1. **Create directory**: `aihub_action/my_action/`
2. **Define action.yml**:
   - `name`, `description`
   - `inputs` (required params)
   - `runs.using: "composite"`
   - `steps` (checkout, setup, execute)
3. **Test**: Reference in test workflow
4. **Document**: Update this AGENTS.md + root README.md
5. **Version**: Tag release after merge to main

## Common Inputs

**working_directory**: Path to scope (e.g., `aihub_agent`)
**github_token**: `${{ secrets.GITHUB_TOKEN }}`
**sonar_token**: `${{ secrets.SONAR_TOKEN }}`
**coverage_file**: Path to coverage report

## Testing Actions

**Local**: Not directly possible. Test by:
1. Push to branch in `aihub-core`
2. Reference in customer repo: `uses: bbvch-ai/aihub-core/aihub_action/my_action@my-branch`
3. Trigger workflow, observe results

## Pre-Commit

```bash
# No code quality tools (YAML only)
# Validate with yamllint (optional)
```

## Essential Files

- All actions: `/home/user/aihub-core/aihub_action/*/action.yml`
- Example: `/home/user/aihub-core/aihub_action/lint_backend/action.yml`

## Quick Reference

**Use existing action**:
```yaml
- uses: bbvch-ai/aihub-core/aihub_action/<action_name>@main
  with:
    input_name: "value"
```

**Create new action**:
1. `mkdir aihub_action/my_action`
2. Create `action.yml` with `name`, `inputs`, `runs`
3. Test in customer repo workflow
4. Merge to main, tag release
