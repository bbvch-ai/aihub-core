---
title: Development Setup
index: 0
---

# Developer Setup Guide

This guide provides detailed, step-by-step instructions for setting up the AI-Hub development environment. It is designed to walk you through installing the necessary tools, configuring your IDE (specifically JetBrains PyCharm and WebStorm), and getting the codebase up and running locally.

-----

## Install Required & Recommended Tools

Before you begin, you need to install several tools. Follow the instructions for your operating system.

  - **JetBrains Toolbox**: This is the recommended way to install and manage your IDEs.

      - Download from the [JetBrains Toolbox website](https://www.jetbrains.com/toolbox-app/).
      - Install PyCharm for backend development and WebStorm for frontend development.
      - *bbv employees*: You can request a JetBrains license via [YouTrack](https://youtrack.bbv.ch/newIssue?project=issues).

  - **Git**: The version control system for our project.

      - You can download it [directly](https://git-scm.com/) or install it through your IDE. JetBrains IDEs have excellent built-in Git support.

  - **Python (3.11) via Miniconda**: We use Miniconda to create isolated Python environments.

      - Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
      - **Important**: During installation, ensure you add Miniconda to your system's PATH.
      - To verify the installation, open a terminal and run: `conda --version`.
      - > **Note**: Miniconda is used only to create the virtual environment and install the base Python version. Package management within the environment is handled by Poetry.

  - **make (Windows only)**: A tool for automating tasks.

      - Download `make` from [GnuWin32](http://gnuwin32.sourceforge.net/packages/make.htm).
      - Add the `bin` directory from the installation folder to your system's PATH.
      - Verify by running: `make --version`.

  - **Poetry**: The dependency management tool for our Python projects.

      - Follow the installation instructions on the [official Poetry website](https://python-poetry.org/docs/).
      - Verify by running: `poetry --version`.

  - **Docker**: For running our application stack in containers.

      - Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
      - If you encounter a `wsl --update` error on Windows that isn't resolved by running the command, refer to this [Stack Overflow solution](https://stackoverflow.com/questions/78879806/docker-desktop-wsl-update-failed).
      - Verify by running: `docker --version`.

  - **Node.js (LTS) through NVM**: We use NVM to manage Node.js versions for frontend development.

      - Install NVM for [Windows](https://github.com/coreybutler/nvm-windows/releases) or [Linux/macOS](https://github.com/nvm-sh/nvm).
      - Install the latest Long-Term Support (LTS) version of Node.js by running: `nvm install --lts`.
      - Activate the installed version with the `nvm use <version_number>` command shown after installation.
      - Verify by running `node --version` and `npm --version`.

  - **Azure CLI**: For managing Microsoft Azure resources from the command line.

      - Follow the [Azure CLI installation guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli).
      - Verify by running: `az --version`.

  - **Additional Tools**:

      - **MongoDB Compass**: A GUI for managing MongoDB. [Download here](https://www.mongodb.com/products/compass).
      - **Postman**: For testing our APIs. [Download here](https://www.postman.com/).
      - **Bot Framework Emulator**: For testing chatbots. [Download here](https://github.com/microsoft/BotFramework-Emulator).

-----

## Set Up the Codebase

### Clone Repositories

First, clone the necessary repositories into a local directory.

  - **aihub-core**: The core services and libraries for the AI-Hub.
    ```bash
    git clone https://github.com/bbvch-ai/aihub-core
    ```
  - **aihub-bbv**: The customer repository for bbv (for bbv employees only).
    ```bash
    git clone https://github.com/bbvch-ai/aihub-bbv
    ```

### Set Up Backend Services (PyCharm)

The `aihub-core` repository is a monorepo containing multiple independent microservices (e.g., `aihub_api`, `aihub_agents`). The following steps explain the recommended way to set up the project in PyCharm for a smooth development experience.

1.  **Open the `aihub-core` Project**:

      - Start PyCharm and select **File \> Open**.
      - Navigate to the `aihub-core` directory you cloned and open it as the main project.

2.  **Attach Microservices as Projects**:

      - Each folder in `aihub-core` with a `pyproject.toml` file is a separate microservice. You need to attach each one to your PyCharm workspace.
      - For each microservice (e.g., `aihub_api`, `aihub_bot`, `aihub_lib`, `aihub_agent`, `aihub_pipeline`):
          - Go to **File \> Open...**.
          - Select the microservice folder (e.g., `aihub_agent`).
          - In the dialog that appears, choose **Attach**. This adds it to your current project window.

3.  **Set Up Poetry Environments for Each Microservice**:

      - You must configure a separate Poetry environment for each attached microservice to keep dependencies isolated.
      - For each attached project:
          - Go to **File \> Settings \> Project: aihub-core \> Python Interpreter**.
          - In the top-left dropdown, select the microservice you want to configure (e.g., `aihub_agent`).
          - Click **Add Interpreter \> Add Local Interpreter**.
          - In the new window, select **Poetry Environment**.
          - For the **Base interpreter**, select the Python executable from your Miniconda installation (e.g., in `AppData/Local/miniconda3`).
          - PyCharm should automatically find your **Poetry executable**. If not, locate the `poetry.exe` file.
          - Click **OK** to create the environment. PyCharm will automatically run `poetry install`.

4.  **Set Up Project Dependencies in PyCharm**:

      - Since services like `aihub_api` and `aihub_agent` depend on `aihub_lib`, you need to tell PyCharm about this relationship for features like code navigation and autocompletion to work correctly.
      - Go to **File \> Settings \> Project: aihub-core \> Project Dependencies**.
      - For each microservice project (`aihub_api`, `aihub_bot`, `aihub_agent`, `aihub_pipeline`), check the box for `aihub_lib` to mark it as a dependency.

### Set Up Frontend Services

  - Navigate to the `aihub_web` folder.
  - Follow the specific instructions in the `README.md` file located inside that directory to set up the frontend.

### Configure Environment Variables

  - The project requires `.env` files for configuration, which contain sensitive keys and settings.
  - You must request the necessary `.env` files from a team member.
  - Place the received `.env` files in the root directories of the corresponding backend and frontend projects.

-----

## First Steps: Running the Application

### Start the Infrastructure with Docker

1.  Make sure Docker Desktop is running.
2.  Navigate to the root of the `aihub_agent` directory in your terminal.
3.  Run the following command to start the core services (Phoenix for tracing, NATS for messaging, and MongoDB):
    ```bash
    docker compose up
    ```
4.  To start the services including the local Milvus vector database, use this command instead:
    ```bash
    docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml up
    ```
5.  Alternatively, PyCharm's Docker integration allows you to simply click the green play button next to the services in your `docker-compose.yml` file.

### Explore the Playground

  - Once the services are running, explore the `playground` directories within each microservice. These contain scripts and notebooks for testing and experimenting with the code in a sandbox environment. This is a great way to understand how different components work.

-----

## IDE Configuration and Plugins (Recommended)

To optimize your development workflow, we recommend installing the following plugins and enabling specific settings in your JetBrains IDE.

### Useful PyCharm Plugins & Settings

  - **Plugins**:

      - [GitHub Copilot](https://plugins.jetbrains.com/plugin/17718-github-copilot): AI-powered code completion.
      - [SonarLint](https://www.sonarsource.com/products/sonarlint/features/jetbrains/): Real-time code quality and security checks.
      - **Database Tools and SQL**: (Included by default) Use this to connect to and manage MongoDB directly from PyCharm.
      - **Docker**: (Included by default) Interact with Docker containers and services from within the IDE.

  - **Settings**:

      - **Black Code Formatter**: Enable Black to automatically format your Python code. Find the setting under **Tools \> Black**.
      - **Code With Me**: A built-in tool for collaborative development and pair programming.
      - **Auto-Format on Save**:
        1.  Go to **File \> Settings \> Tools \> Actions on Save**.
        2.  Check the boxes for `Reformat code` and `Run Black`.
      - **Pre-Commit Checks**:
        1.  In the Commit tool window, click the settings (gear) icon.
        2.  Under **Commit Checks**, enable `Reformat code` and `Perform SonarQube for IDE analysis`.

### Useful WebStorm Plugins

  - [GitHub Copilot](https://plugins.jetbrains.com/plugin/17718-github-copilot)
  - [SonarLint](https://www.sonarsource.com/products/sonarlint/features/jetbrains/)
  - **EsLint**: Enable this to automatically lint your JavaScript/TypeScript code. You can configure it to run on save under **Settings \> Languages & Frameworks \> JavaScript \> Code Quality Tools \> ESLint**.