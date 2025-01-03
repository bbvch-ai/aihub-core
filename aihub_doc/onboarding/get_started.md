# Getting Started: Developer Onboarding Guide

This guide will help you quickly set up your environment and install necessary tools to start contributing effectively to the AI-Hub. 
For deeper insights into the architecture and workflows, refer to the documentation in `aihub_doc`. 

---

## **1. Install Required Tools**


- **JetBrains Toolbox**: Install and manage IDEs like PyCharm (backend) and WebStorm (frontend).
  - Request a license via [YouTrack](https://youtrack.bbv.ch/newIssue?project=issues) .
- **Git**: You may install it in your IDE under Version Control and link your account or download it ([Download Git](https://git-scm.com/))
- **Python (3.11)**: Install directly or use [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
- **Docker**: Containerization tool ([Download Docker](https://www.docker.com/products/docker-desktop/)).
  - Verify: `docker --version`
- **Node.js (LTS)** and **NVM**: For frontend development ([Download Node.js](https://nodejs.org/)). Install NVM from [NVM GitHub](https://github.com/nvm-sh/nvm).
  - Set Node.js version: `nvm install <node_version>` and `nvm use <node_version>`
- **MongoDB Compass**: GUI for managing MongoDB ([Download MongoDB Compass](https://www.mongodb.com/products/compass)).
- **Azure CLI**: Manage Azure resources ([Download Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)).
  - Verify: `az --version`
- **Postman**: For API testing.

---

## **2. Set Up the Codebase**

### **2.1 Clone Repositories**
Clone the following repositories:
- **aihub-core**: Core services for the AI-Hub.
    ```bash 
    git clone https://github.com/bbvch-ai/aihub-core
    ```
- **aihub-bbv**: bbv customer repo
    ```bash
    git clone https://github.com/bbvch-ai/aihub-bbv
    ```
- **ai-hub**: Legacy repository
    ```bash
    git clone https://github.com/bbvch-ai/ai-hub
    ```

### **2.2 Install Dependencies**

Each folder in the `aihub-core` repository represents a **microservice**. 
To ensure proper isolation and compatibility, follow these steps for each folder:

1. **Open Each Folder in a Separate IDE**:
   - Recommendation: Use PyCharm for backend services and WebStorm for frontend services.

2. **Set Up an Environment for Each Microservice**:

   **In PyCharm:**
   - Open the microservice folder as a new project.
   - Go to **File > Settings > Project: <ProjectName> > Python Interpreter** (on macOS: **PyCharm > Preferences > Project > Python Interpreter**).
   - Click on the gear icon and select **Add** > **Poetry Environment**.
     - **Environment Location**: Use a unique environment name, e.g., `aihub_agent`.
     - **Python Version**: Select Python 3.11. If you are using Miniconda, select a conda environment with Python 3.11.
   - Apply and set the environment.
   - Open the PyCharm terminal and initialize Poetry within the environment:
     ```bash
     poetry install
     ```

3. **Repeat** this process for each folder (e.g., `aihub_lib`, `aihub_agent`, `aihub_pipeline`).

4. **Frontend Setup:** Navigate to the aihub_web folder
   - Follow the instructions in the `README.md` file to set up the frontend.

### **2.3 Configure Environment Variables**
- Request `.env` files from the team.
- Place them in the root directories of backend and frontend projects.

---

## **3. Verify Setup**

1. **Start the Backend**:
   

2. **Start the Frontend**:
   - Navigate to `aihub_web` and run:
     ```bash
     pnpm dev
     ```

3. **Access the System**:
   - Confirm that both the backend and frontend are running successfully by accessing the provided local URLs.

---

## **4. First Tasks**
### **4.1. Read the Documentation**
- Explore the `aihub_doc` folder in the `aihub-core` repository. 
- Feel free to read up on any other resource used in the project e.g. LlamaIndex, FastAPI, Nuxt.js, etc.

### **4.2. Get familiar with Azure Infrastructure**
Most projects use Microsoft Azure. Therefore, it makes sense to get familiar with the Azure Portal and the resources we use.
- Ensure you have access to the Azure portal (https://portal.azure.com/#home) and the resource groups we use:
  - **aihub-dev-rg-che**
  - **aihub-prod-rg-che**
- Each resource group has:
  - **Cosmos MongoDB**: All organizations with their LLMs, agents, and documents are stored here. You may use MongoDB Compass to access the data.
    - Prod: aihub-prod-cos-che
    - Dev: aihub-dev-cos-che
  - **Azure Search Service (Vector Store)**: This service is used to store and search for vector embeddings.
    - Prod: aihub-prod-srch-che
    - Dev: aihub-dev-srch-che
  - **Data Lake Storage**: This is used to store data to be processed by the pipelines.
    - Prod: aihubprodstchedatalake
    - Dev: aihubdevstchedatalake


### 4.3. Explore the Codebase + Playground
- **Codebase**: Explore the codebase to understand the structure and the services provided.
- **Playground**: Use the `playground` directories in the services to test and experiment with the code.

### 4.4 Development Workflow
- Create a new branch
-

### 4.5 Testing
The AI-Hub uses pytest with pytest-bdd for behavior-driven development. 
Create the following structure for tests:
```
tests/
├── features/
│   ├── agent.feature
├── steps/
│   ├── test_agent.py
```
---

## **5. Advanced Resources**

### **5.1 Dagster for Pipelines**
The **aihub_pipeline** folder utilizes Dagster for data orchestration. Dagster enables structured and transparent workflows for:
- **Data Ingestion**: Handling large volumes of data from sources like Azure Data Lake.
- **Processing**: Converting raw data into usable formats (e.g., vector embeddings for AI models).
- **Scheduling**: Automating regular updates to keep pipelines fresh.

**Learning Resources**:
- [Dagster Documentation](https://docs.dagster.io/)
- [Dagster Tutorials](https://docs.dagster.io/getting-started)

### **5.2 NATS for Event-Driven Architecture**
The AI-Hub leverages NATS for high-performance, event-driven communication between components.
- **Use Cases**:
  - Facilitates asynchronous communication between the backend, agents, and pipelines.
  - Provides message durability and persistence with JetStream.
  - Enables scalability through topic-based routing.

**Learning Resources**:
- [NATS Documentation](https://nats.io/documentation/)
- [NATS JetStream Guide](https://docs.nats.io/nats-concepts/jetstream)

---

## **6. Further Resources**
- **AIHub Documentation**: Refer to the `aihub_doc` folder in the `aihub-core` repository.
- [Python Documentation](https://docs.python.org/3/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/en/stable/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Nuxt.js Documentation](https://nuxt.com/docs)
- [pytest-bdd Documentation](https://pytest-bdd.readthedocs.io/en/latest/)
- [shadcn Documentation](https://ui.shadcn.com/docs)

---


