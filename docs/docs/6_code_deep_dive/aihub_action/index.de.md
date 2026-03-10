---
title: Github Actions
index: 7
---

# 🚀 Swiss AI Hub Actions - Reusable Actions for CI/CD (GitHub workflows)

::: info
These actions are a collection of modular GitHub Actions designed to automate and standardize CI/CD workflows across
customer repositories. Each action is focused on a specific task such as building images, linting code, running tests,
posting coverage comments, and more.
:::

## 📁 Directory Structure

The repository is organized as follows:

```
aihub_action/
│
├── build_image/
│   └── action.yml             # Builds and pushes Docker images
│
├── lint_backend/
│   └── action.yml             # Lints backend code using Black
│
├── lint_frontend/
│   └── action.yml             # Lints frontend code using ESLint
│
├── pytest_coverage_comment/
│   └── action.yml             # Posts pytest coverage reports as PR comments
│
├── review_pr/
│   └── action.yml             # Provides AI-assisted pull request reviews
│
├── sonarcloud_scan/
│   └── action.yml             # Runs SonarCloud analysis for code quality
│
├── test_backend/
│   └── action.yml             # Runs backend tests with coverage
```

## 📝 Defining an Action (`action.yml`)

::: tip Action Definition
Here's an example of how to define an action to lint backend code using Black. This reusable action installs Python,
checks out the repository, and runs the linter.
:::

### 📝 Example: `lint_backend/action.yml`

```yaml
name: Lint Backend
description: Lints backend Python code using Black.

inputs:
  github_token:
    description: GitHub token for authentication.
    required: true
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

    - name: Install Black
      run: pip install black

    - name: Run Black Linter
      run: black ${{ inputs.working_directory }}
```

### 🔄 Example: Using the Action in a Workflow

::: info
To use this action in a repository, reference it in a GitHub workflow file.
:::

#### 📝 Corresponding GitHub Workflow File: `.github/workflows/lint_backend.yml`

```yaml
name: Lint Backend

on:
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Lint Backend Code
        uses: bbvch-ai/swiss-ai-hub/aihub_action/lint_backend/action.yml@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          working_directory: "agents"
```

::: tip Key Points
1. The reusable action is stored in `aihub_action/lint_backend/action.yml`.
2. The workflow file references this action using the `uses` keyword.
3. Inputs like `github_token` and `working_directory` are passed to the action.
:::

## ✅ Best Practices

::: warning Best Practices
- Ensure each action is focused on a single task.
- Test actions thoroughly before integrating them into repositories.
- Use descriptive names and clear documentation in `action.yml` files.
- Use tagged versions (`@v1.0.0`) instead of `@main` in workflows for stability.
- Store sensitive data, such as `GITHUB_TOKEN`, in the repository's Secrets.
:::
