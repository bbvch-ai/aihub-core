from .api.chats import ChatsClient
from .api.files import FilesClient
from .api.knowledge import KnowledgeClient
from .api.users import UsersClient

__all__ = ["OpenWebuiClient"]


class OpenWebuiClient:
    """
    Main client for the OpenWebUI API.

    Provides access to all API endpoints through resource-specific clients.
    Currently includes user management, file operations, knowledge base endpoints,
    and chat management.

    Example:
        ```python
        client = OpenWebuiClient(token="your-token")

        # Access users API
        users = await client.users.get_users()

        # Access files API
        files = await client.files.list_files()

        # Access knowledge API
        knowledge_bases = await client.knowledge.get_knowledge_bases()

        # Access chats API
        chats = await client.chats.get_chats_list()
        ```
    """

    def __init__(self, base_url: str = "http://localhost:8080", token: str | None = None, timeout: int = 10):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout

        # Initialize API resource clients
        self.users = UsersClient(base_url, token, timeout)
        self.files = FilesClient(base_url, token, timeout)
        self.knowledge = KnowledgeClient(base_url, token, timeout)
        self.chats = ChatsClient(base_url, token, timeout)
        # Additional resource clients will be added here
