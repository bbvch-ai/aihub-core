
# 8. Backend / API

## 8.1 FastAPI Architecture

> tldr; The FastAPI-based backend is the glue that holds the user-facing frontend and the agent-based event-driven architecture together. By providing secure, authenticated access to resources, orchestrating complex interactions through simple REST and WebSocket endpoints, and coupling real-time event streaming with persistent historical storage, the backend delivers a scalable and transparent environment for AI-driven solutions.
> 
> As a result, clients can interact with agents confidently, knowing that authentication, authorization, event reliability, and workflow orchestration are handled elegantly by the backend.


The backend of the AI-Hub serves as the crucial bridge between users, agents, and other infrastructure components. While agents run as independent microservices consuming and producing events, the backend ties everything together to create a cohesive and secure user experience. It provides API endpoints for managing threads, agents, user sessions, and events, as well as authenticating and authorizing requests. Additionally, it manages WebSocket connections to deliver real-time event streams to frontends.

### API Controllers and Routes

**Design Principles:**
- The backend is implemented using **FastAPI**, a modern, high-performance Python web framework.
- FastAPI embraces type hints and automatic documentation, making the API self-describing and easier to maintain.
- A consistent routing structure ensures that all endpoints follow a logical, predictable pattern—e.g., `/api/v1/thread/`, `/api/v1/agent/`, `/api/v1/event/`.

**Key Responsibilities:**
1. **Thread Management:**  
   Endpoints allow clients to create, list, and manage threads. A thread is a logical grouping of related interactions—like a conversation or a workflow context.
   
2. **Agent Discovery & Integration:**  
   The backend provides routes to discover available agents. Clients can attach agents to threads, remove them, or configure their properties.
   
3. **Event Retrieval & History:**  
   While the frontend often relies on WebSocket streams for real-time updates, the backend also offers REST endpoints to fetch historical events. This ensures that when a user first loads a page, they receive past events, and only subsequent updates come via WebSocket.
   
4. **User Actions:**  
   The backend can accept user inputs—like a user message event or a human-in-the-loop decision—and publish them as events to the underlying event system, triggering agents to process them.

**Extensibility and Modular Design:**
- Controllers are separated by domain—e.g., a `ThreadController`, `AgentController`, `EventController`. Each controller manages a specific resource type, making it easy to add new controllers or update existing ones without disrupting the entire API.
- Shared utilities (like authentication, database connections, or configuration management) are injected via dependencies, reducing tight coupling.

### Authentication & Authorization (OAuth2/OpenID Connect)

**Securing Access:**
- The AI-Hub backend often runs in a corporate or enterprise environment. Ensuring secure and compliant access to resources is mandatory.
- **OAuth2/OpenID Connect:**  
  The backend integrates with OAuth2 identity providers (e.g., Azure AD, Keycloak), requiring users to authenticate before accessing private endpoints. An authenticated user receives a token, which is validated by the backend to ensure only authorized sessions can interact with agents and data.
  
**Role-Based Access Control:**
- **Roles and Permissions:**  
  Depending on the client’s environment, the backend can enforce role-based access control. For example, only users with admin roles might modify thread participants or attach new agents.  
- **Token Validation & Claims:**  
  The backend extracts claims from the user’s JWT tokens (provided via OAuth2/OIDC flow) to determine user identity, roles, and permissions. This ensures fine-grained control over who can perform which actions.

**Seamless Integration with Frontend:**
- The frontend acquires a token during its login flow. Each subsequent request to the backend includes this token, ensuring every API call is authenticated.
- The backend responds with appropriate HTTP status codes (e.g., `401 Unauthorized` if the token is invalid or `403 Forbidden` if the user lacks required permissions), providing clear feedback to the UI and guiding appropriate user actions like re-authentication.

### Role of the Backend in Event Forwarding

**Event-Driven Backend:**
- As described in [Section 4.2 (Event-Driven Architecture)](4_architectural_overview.md#42-event-driven-architecture), agents communicate via NATS and JetStream events. However, the frontend needs an HTTP or WebSocket interface to receive these events.
- The backend acts as a translator: it subscribes to relevant subjects on NATS, listens for events, and forwards them to the frontend via a WebSocket. This approach decouples the frontend from the messaging infrastructure, letting it communicate solely with the backend.

**Offline History and Event Storage:**
- To show a conversation’s past context, the backend must persist events in a database (e.g., MongoDB). When a user loads a thread’s page, the backend retrieves the entire event history from the database and returns it via a REST endpoint.
- Any new events that arrive after the initial page load are delivered through the WebSocket, ensuring the UI stays up-to-date without forcing full page reloads.

**Ensuring Reliable Delivery:**
- If the user disconnects or closes the browser, the events aren’t lost. When they return, the backend can replay all missed events from the database.
- This hybrid approach—REST for initial fetching and WebSocket for streaming—provides a robust user experience. Large historical data sets are efficiently loaded upfront, and then minimal real-time updates keep the interface current.

### Putting It All Together

A typical user interaction might look like this:

1. **User Authentication:**  
   The user logs in via an OAuth2 flow, obtains an access token, and the frontend stores this token securely.

2. **Thread and Agent Setup:**  
   The frontend calls the backend’s `GET /api/v1/thread` endpoint to list available threads, `GET /api/v1/agent/discover` to find agents, and `POST /api/v1/thread/{id}/agents` to attach an agent to a thread.

3. **Event Retrieval and Live Updates:**  
   When viewing a thread, the frontend uses `GET /api/v1/event` to load past events and then opens a WebSocket (`/api/v1/event/ws`) to receive new events as they happen.

4. **User Input:**  
   If the user sends a new message (`UserMessageEvent`) or responds to a human-in-the-loop question (`HumanInTheLoopResponseEvent`), the frontend posts these to the backend. The backend publishes them into NATS, triggering agent steps. When the agent responds, the backend forwards these events to the frontend WebSocket.

The backend’s architecture ensures all these steps are secure, well-organized, and efficient, allowing the frontend and agents to operate smoothly without worrying about infrastructure details.

