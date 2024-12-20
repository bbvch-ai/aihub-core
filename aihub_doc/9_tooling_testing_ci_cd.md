# 9. Tooling, Testing, and CI/CD

## 9.1 Development Environment Setup

> tldr; A developer onboarding to the AI-Hub might follow these steps:
>
> 1. **Install Prerequisites:** Docker, NVM, PNPM, and Poetry.
> 2. **Clone the Repository:** Check out the AI-Hub codebase.
> 3. **Run Docker Compose:** `docker compose up` starts services like phoenix and NATS.
> 4. **Set Up Frontend Environment:** `nvm use <node_version>`, `pnpm install`, and `pnpm dev` to run the frontend.
> 5. **Python Virtual Environment:** `poetry install` to set up the backend and agent Python environment.
> 6. **Open in IDE:** Launch PyCharm (for backend and agent code) and WebStorm (for frontend code), both of which can connect to the Docker environment and integrate with Poetry/PNPM seamlessly.
> 
> This well-structured setup ensures a high level of consistency, reduces friction, and empowers developers to quickly become productive. As a result, the AI-Hub team can focus on solving business problems and improving agent logic rather than wrestling with environment issues.


A smooth and consistent development environment is essential for maintaining high productivity and code quality. In the AI-Hub, we leverage a combination of containerization (Docker), environment managers (Poetry, NVM, PNPM), and modern IDEs (JetBrains tools like PyCharm and WebStorm) to create a reliable and reproducible setup. This ensures that developers can quickly get started, test changes locally, and maintain a stable workflow across multiple projects and environments.

### Local Setup with Docker Compose

**Why Docker Compose?**  
- The AI-Hub’s architecture involves multiple external services, like phoenix for tracing and NATS for messaging.
- Managing each component manually would be time-consuming and error-prone. Docker Compose allows us to define all these services in a single configuration file, enabling developers to spin up the entire stack locally with a single command.

**Typical Services:**
- **NATS & JetStream:** Core messaging infrastructure for event-driven communication.
- **Phoenix (OpenInference & Observability):** Tools for tracing and debugging agent workflows.
- **Databases (Postgres):** Databases required by tools like phoenix or dagster.

**Workflow:**
1. **Clone the Repository:**  
   Developers clone the AI-Hub project(s) they need.
   
2. **Launch the Stack:**  
   Run `docker compose up` (or `docker-compose up`) from the project’s root directory. This starts all external defined services, ensuring the environment is consistent across all team members’ machines.

### Node Version Manager (NVM) and PNPM for Frontend

**NVM:**
- The frontend relies on Node.js for building and running the Nuxt/Vue application.
- **NVM (Node Version Manager)** ensures that everyone uses the same Node.js version. This prevents compatibility problems caused by different Node versions on different machines.

**PNPM:**
- PNPM is a fast, disk space-efficient package manager for Node.js.
- Compared to NPM or Yarn, PNPM creates a single store of packages, linking dependencies rather than installing duplicates. This reduces disk usage and improves installation speeds.
- The AI-Hub frontend defines its dependencies in a `package.json`. Running `pnpm install` fetches all required libraries. After this, you can run `pnpm dev` to start the frontend locally.

**Local Frontend Setup:**
1. **Install NVM:** Follow instructions from [https://github.com/nvm-sh/nvm](https://github.com/nvm-sh/nvm).
2. **Set Node Version:** `nvm install <node_version>` and `nvm use <node_version>` to match the project's required Node.js version.
3. **Install PNPM:** `npm install -g pnpm`.
4. **Install Dependencies:** `pnpm install`.
5. **Run the Frontend:** `pnpm dev` will launch the Nuxt 3 application on a local port.

### Poetry for Python Environment Management

**Why Poetry?**
- The backend, agents, and pipelines are Python-based. Python’s flexible ecosystem can lead to dependency conflicts if not managed carefully.
- **Poetry** is a modern Python dependency manager that ensures predictable installs and isolated virtual environments.

**Setting Up Poetry:**
1. **Install Poetry:** Follow instructions at [https://python-poetry.org/](https://python-poetry.org/) to install Poetry on your machine.
2. **Install Dependencies:**  
   Navigate to the project directory containing a `pyproject.toml` file and run `poetry install`.
   Poetry sets up a virtual environment with all required Python packages.
3. **Activating the Environment:**  
   Use `poetry shell` to enter the virtual environment or prefix commands with `poetry run` to execute them in a controlled environment.
   
**Benefits:**
- **Consistent Environments:** Every developer uses the same Python dependency versions, reducing dependency-related bugs.
- **Easy Updates:** Adjusting dependencies in `pyproject.toml` and running `poetry update` keeps the environment up-to-date.

### JetBrains IDEs: PyCharm and WebStorm

**Why JetBrains IDEs?**
- **PyCharm:** Ideal for Python backend and agent development, offering robust debugging, code completion, and integrated test runners.
- **WebStorm:** Excellent for frontend development, providing intelligent code completion, built-in linters, and integration with PNPM and NVM.

**Integration Tips:**
- **Docker Integration:** JetBrains IDEs can connect to Docker and Docker Compose services directly from within the IDE. You can run and debug services, inspect containers, and manage logs without leaving your development environment.
- **Python and Poetry Integration:** PyCharm can detect and use Poetry’s virtual environments, ensuring that all linting and debugging occurs with the correct Python dependencies.
- **Node.js Integration in WebStorm:** WebStorm can use NVM-installed Node versions and PNPM directly, simplifying the frontend development workflow.

## 9.2 Code Quality and Standards

> tldr; Code quality and standards are integral to the AI-Hub’s philosophy of building reliable, maintainable AI solutions. Through rigorous linting, formatting, and type-checking, combined with advanced static analysis and AI-assisted code reviews, the project ensures that each contribution strengthens the codebase rather than weakening it.
> 
> This disciplined approach fosters a healthier development environment, enabling the AI-Hub team to focus on delivering value, innovation, and trusted AI solutions to clients.


Maintaining a high level of code quality across multiple repositories, languages, and contributors is essential for the longevity and reliability of the AI-Hub. To achieve this, the project enforces strict coding standards, linting rules, formatting guidelines, and type checks. Additionally, tools like SonarCloud and Codeium integrate automated quality checks and AI-assisted code reviews, ensuring that each pull request meets stringent quality gates before merging.

### Linting, Formatting, and Type-Checking

**ESLint (Frontend JavaScript/TypeScript):**
- **What It Does:** ESLint enforces consistent code style and detects common errors in JavaScript/TypeScript code. It can catch issues like unused variables, incorrect imports, or potential runtime errors.
- **Configuration:** The AI-Hub frontend defines a strict ESLint configuration, requiring developers to follow best practices and coding conventions. If ESLint detects violations, they appear as warnings or errors, prompting a quick fix.
- **Integration with CI/CD:** ESLint runs automatically as part of CI, ensuring no code with lint errors is merged into the main branch.

**Black (Python Formatting):**
- **What It Does:** Black is an uncompromising Python code formatter that ensures every Python file follows a consistent style.
- **Benefits:** By taking formatting decisions out of human hands, Black reduces code review friction. Developers no longer debate over single or double quotes or spacing details—Black settles it uniformly.
- **Running Black:** Executed either manually (e.g., `black .`) or in CI/CD pipelines, guaranteeing formatting consistency across all Python files.

**MyPy (Python Type Checking):**
- **What It Does:** MyPy checks Python code against defined type hints, ensuring that functions and variables are used as intended.
- **Why It Matters:** Without static typing, Python can be error-prone in large codebases. MyPy helps catch type errors early, improving reliability and maintainability.
- **Strict Mode:** The AI-Hub typically uses MyPy in strict mode, encouraging thorough type annotations and reducing potential runtime errors.

**Ruff (Fast Python Linter):**
- **What It Does:** Ruff is a fast Python linter that can detect code smells, style inconsistencies, and potential errors.
- **Complementing Black and MyPy:** While Black handles formatting and MyPy checks types, Ruff focuses on linting rules. Together, they create a robust quality assurance pipeline for Python code.
- **Speed and Efficiency:** Ruff’s performance makes it suitable for running on every commit, providing quick feedback to developers.

### SonarCloud & Codeium

**SonarCloud:**
- **Purpose:** SonarCloud is a cloud-based code quality and security tool. It performs deep static analysis on the codebase, highlighting code smells, potential security vulnerabilities, and maintainability issues.
- **Quality Gates:** SonarCloud defines “quality gates”—criteria that code must meet to be considered high quality. If a pull request fails a quality gate (e.g., it introduces new code smells or lowers test coverage), the merge is blocked until the issues are resolved.
- **Long-Term Metrics:** Over time, SonarCloud provides a dashboard of code quality metrics—like technical debt, coverage trends, and duplication—helping the team continuously improve.

**Codeium (AI-Assisted Code Checks):**
- **What It Does:** Codeium is an AI-driven code review assistant that analyzes pull requests and suggests improvements, alternative approaches, or identifies subtle issues that might be missed by traditional linters or static analyzers.
- **Benefits:**  
  - **Speed:** Codeium’s AI-powered suggestions help developers quickly spot improvement opportunities.
  - **Learning Aid:** It can also serve as an educational tool, explaining why certain approaches are better than others.
- **Integration in CI:** Just like SonarCloud, Codeium hooks into the CI/CD pipeline. Its suggestions appear as comments on pull requests, providing actionable insights for developers to improve their code.

### CI/CD Integration

All these tools—ESLint, Black, MyPy, Ruff, SonarCloud, and Codeium—are integrated into the project’s CI/CD pipelines. A typical pipeline might:

1. **Install Dependencies:** Ensure the correct versions of Node.js, Python, and Poetry are available.
2. **Run Linters and Formatters:** ESLint for the frontend, Black, Ruff, and MyPy for the backend and agents.
3. **SonarCloud Analysis:** Upload the codebase to SonarCloud for thorough quality scanning.
4. **Codeium Review:** Codeium comments on the pull request with suggestions, if any.

If any step fails—like a lint error, a type mismatch, or a new security hotspot—CI blocks the merge, prompting the developer to address the issues. This ensures that every commit on the main branch meets the team’s quality standards.

### Developer Workflow and Benefits

**Developer Experience:**
- With automated formatting and linting, developers spend less time debating style and more time focusing on logic.
- Type-checking and code quality gates catch bugs early, reducing production incidents and manual debugging efforts.
- Automated AI suggestions help developers learn from best practices and improve their coding skills over time.

**Maintainability and Scalability:**
- As the codebase grows, these tools ensure it remains consistent, stable, and secure.
- By enforcing quality at every stage, the AI-Hub codebase can scale to accommodate new features, agents, and pipelines without devolving into a tangled mess of technical debt.

## 9.3 CI/CD Pipelines

> tldr; The CI/CD pipelines orchestrate a seamless, high-confidence workflow from code commit to production release. GitHub Actions provide a flexible and integrated solution for:
> - Running automated tests, linting, and quality checks on every PR and push.
> - Versioning and tagging releases automatically.
> - Deploying complex, multi-service architectures with Pulumi and Docker.
> - Facilitating quick rollbacks in case of issues.
> 
> This well-designed CI/CD pipeline architecture ensures that changes flow smoothly and safely to production, allowing the team to focus on delivering value rather than wrestling with deployment complexities.


Continuous Integration (CI) and Continuous Deployment (CD) form the backbone of a reliable software delivery process. By automating testing, linting, building, and deployment, the AI-Hub ensures that changes are integrated smoothly and that releases can be made frequently and safely. The CI/CD pipelines use **GitHub Actions**—a native GitHub feature—allowing developers to run workflows on every commit, pull request, or release event.

### GitHub Actions: Automated Testing, Linting, and Building

**Triggers and Workflows:**
- **Pull Requests (PRs):** When a developer opens or updates a PR, GitHub Actions automatically run checks—such as linting (ESLint, Black, Ruff), type-checking (MyPy), and testing (pytest)—to ensure that new changes do not break existing functionality.
- **Pushes to Main or Initiative Branches:** On every push to main or certain special branches (like `initiative/*`), actions may increment version tags, run full test suites, and build Docker images.
- **Release Events:** When a new release is created (tagging a new version), CI pipelines trigger deployment jobs that push containers to registries or apply Infrastructure as Code (IaC) changes to cloud resources.

**Quality Gates and Reports:**
- All CI pipelines integrate quality checks. If a test fails, linting rules are violated, or a code quality gate (e.g., SonarCloud analysis) fails, the PR or push is marked as failing, preventing it from merging into main.
- Test coverage reports, generated from pytest and coverage tools, are uploaded as artifacts. SonarCloud scans the code for maintainability issues and security hotspots. Codeium provides AI-assisted code review suggestions directly on the PR.

**Artifact Management:**
- CI pipelines produce artifacts like coverage reports or compiled assets. These artifacts can be downloaded and inspected by developers if needed.
- GitHub Actions also allow for storing and reusing build artifacts (e.g., cached Python virtual environments) across runs to speed up the feedback loop.

### Deployment Scripts: How to Release New Versions and Revert if Necessary

**Automated Versioning and Tagging:**
- A dedicated action increments the project’s version tags whenever code is pushed to `main`.
- This tagging scheme (e.g., `v0.1.0` → `v0.2.0`) ensures that every commit to main corresponds to a semantic version tag, facilitating reproducible builds and releases.

**Docker Image Builds and Releases:**
- Once tagged, workflows build Docker images (for services like Dagster or the API) and push them to GitHub’s Container Registry (GHCR).
- On release creation, a specialized workflow deploys the infrastructure and updates the application’s configuration in Azure via Pulumi scripts. This includes setting environment variables, assigning roles, and restarting services to apply changes.

**Infrastructure as Code (IaC) Integration:**
- Pulumi, run via CI workflows, applies IaC changes. This ensures that deployments to Azure are consistent and version-controlled.
- Separate jobs handle API, Dagster, NATS, and Phoenix deployments. Each environment (like `Api`, `Dagster`, `Nats`, `Phoenix`, and `Stores`) has its own Pulumi stack, managed by these jobs.
- If a deployment fails or must be rolled back, developers can revert to a previous tag. Running the CI pipeline against that older tag redeploys the previous version of the infrastructure and code.

**Controlled Promotion and Rollbacks:**
- By leveraging release branches or tags, the team can promote a tested version to production. If something goes wrong in production, reverting to a previous tag and re-running the deployment job rolls back the changes.
- This approach provides confidence in releases. Every environment (development, staging, production) is managed through consistent CI/CD pipelines, reducing manual intervention and risk of configuration drift.

### Developer Experience and Flow

**A Typical Developer Scenario:**
1. **Create a Feature Branch:** Work is done on `initiative/feature-name`.
2. **Open a PR:** The CI pipeline runs tests, linters, and quality checks. If any fail, the developer fixes the issues and pushes changes.
3. **Code Review and Merge:** Once the CI passes and reviews are done (including AI-assisted suggestions from Codeium), the PR is merged into `main`.
4. **Auto-Tag and Build:** On merging into `main`, an action increments the minor version and creates a tag. Another workflow builds a Docker image, tests it, and publishes it.
5. **Release and Deploy:** Creating a GitHub release triggers the CI to apply IaC changes and update the environment. The API, Dagster, NATS, Phoenix services, and any underlying stores are redeployed with the new version.
6. **Rollback (If Needed):** If an issue arises, revert to an old tag and run the pipeline again, restoring the environment to a known good state.

