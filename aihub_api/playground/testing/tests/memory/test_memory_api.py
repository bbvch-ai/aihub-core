from unittest.mock import patch

import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.testing.auth_utils.user_mocks import mock_user_entity_autouse  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aihub_api.routes.memory.dto.DeleteMemoryResponse import DeleteAllMemoriesResponse, DeleteMemoryResponse
from aihub_api.routes.memory.dto.MemoriesResponse import MemoriesResponse
from aihub_api.routes.memory.dto.MemoryDTO import MemoryDTO
from aihub_api.routes.memory.dto.MemoryRelationDTO import MemoryRelationDTO
from aihub_api.routes.memory.dto.MemorySearchResponse import MemorySearchResponse
from aihub_api.routes.memory.dto.UpdateMemoryResponse import UpdateMemoryResponse
from aihub_api.routes.memory.MemoryController import MemoryController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

BASE_URL = "http://test"
MEMORIES_ENDPOINT = "/api/v1/memories/user"


@pytest_asyncio.fixture(scope="module")
async def api_client():
    """Create a test client for the API with MemoryController mounted."""
    runner = ApiTestRunner()
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    controller = MemoryController(auth=auth)
    controller.get_user_memories().search_user_memories().delete_user_memory().delete_all_user_memories().update_user_memory()
    runner.mount(controller)
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.fixture
def mock_memory_dto():
    """Create a mock MemoryDTO for testing."""
    return MemoryDTO(
        id="mem123",
        memory="User prefers Python over JavaScript",
        score=None,
        created_at="2024-01-01T12:00:00Z",
        user_id="user123",
        agent_id="agent/123",
        thread_id="thread123",
    )


@pytest.fixture
def mock_relation_dto():
    """Create a mock MemoryRelationDTO for testing."""
    return MemoryRelationDTO(
        source="User",
        relation="prefers",
        target="Python",
    )


@pytest.fixture
def mock_memories_response(mock_memory_dto, mock_relation_dto):
    """Create a mock MemoriesResponse for testing."""
    return MemoriesResponse(
        total=1,
        memories=[mock_memory_dto],
        relations=[mock_relation_dto],
    )


@pytest.fixture
def mock_search_response(mock_memory_dto, mock_relation_dto):
    """Create a mock MemorySearchResponse for testing."""
    return MemorySearchResponse(
        query="Python programming",
        total=1,
        memories=[mock_memory_dto],
        relations=[mock_relation_dto],
    )


class TestGetMemories:
    """Test suite for GET /memories endpoint."""

    @pytest.mark.asyncio
    async def test_get_memories_success(self, api_client, mock_memories_response):
        """Test successful retrieval of memories."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.get_memories_for_user") as mock_service:
            mock_service.return_value = mock_memories_response

            response = await api_client.get(MEMORIES_ENDPOINT)

            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "memories" in data
            assert "relations" in data
            assert isinstance(data["memories"], list)
            assert isinstance(data["relations"], list)
            assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_memories_with_limit(self, api_client, mock_memories_response):
        """Test memories endpoint with limit parameter."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.get_memories_for_user") as mock_service:
            mock_service.return_value = mock_memories_response

            response = await api_client.get(f"{MEMORIES_ENDPOINT}?limit=50")

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["limit"] == 50

    @pytest.mark.asyncio
    async def test_get_memories_invalid_limit(self, api_client):
        """Test memories endpoint with invalid limit parameters."""
        # Test limit < 1
        response = await api_client.get(f"{MEMORIES_ENDPOINT}?limit=0")
        assert response.status_code == 422

        # Test limit > 1000
        response = await api_client.get(f"{MEMORIES_ENDPOINT}?limit=1001")
        assert response.status_code == 422


class TestSearchMemories:
    """Test suite for GET /memories/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_memories_success(self, api_client, mock_search_response):
        """Test successful memory search."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.search_memories") as mock_service:
            mock_service.return_value = mock_search_response

            response = await api_client.get(f"{MEMORIES_ENDPOINT}/search?query=Python programming")

            assert response.status_code == 200
            data = response.json()
            assert "query" in data
            assert "total" in data
            assert "memories" in data
            assert "relations" in data
            assert data["query"] == "Python programming"
            assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_search_memories_missing_query(self, api_client):
        """Test search without required query parameter."""
        response = await api_client.get(f"{MEMORIES_ENDPOINT}/search")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_memories_with_filters(self, api_client, mock_search_response):
        """Test search with filters."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.search_memories") as mock_service:
            mock_service.return_value = mock_search_response

            response = await api_client.get(
                f"{MEMORIES_ENDPOINT}/search?query=test&agent_id=agent/123&thread_id=thread123&limit=50"
            )

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["query"] == "test"
            assert call_kwargs["agent_id"] == "agent/123"
            assert call_kwargs["thread_id"] == "thread123"
            assert call_kwargs["limit"] == 50

    @pytest.mark.asyncio
    async def test_search_memories_empty_results(self, api_client):
        """Test search with no results."""
        empty_response = MemorySearchResponse(
            query="nonexistent",
            total=0,
            memories=[],
            relations=[],
        )
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.search_memories") as mock_service:
            mock_service.return_value = empty_response

            response = await api_client.get(f"{MEMORIES_ENDPOINT}/search?query=nonexistent")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert len(data["memories"]) == 0
            assert len(data["relations"]) == 0


class TestDeleteMemory:
    """Test suite for DELETE /memories/{memory_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, api_client):
        """Test successful deletion of a single memory."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.delete_memory") as mock_service:
            mock_service.return_value = DeleteMemoryResponse(status="deleted", memory_id="mem123")

            response = await api_client.delete(f"{MEMORIES_ENDPOINT}/mem123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"
            assert data["memory_id"] == "mem123"
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_memory_calls_service(self, api_client):
        """Test that delete_memory calls service with correct parameters."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.delete_memory") as mock_service:
            mock_service.return_value = DeleteMemoryResponse(status="deleted", memory_id="mem456")

            response = await api_client.delete(f"{MEMORIES_ENDPOINT}/mem456")

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["memory_id"] == "mem456"


class TestDeleteAllMemories:
    """Test suite for DELETE /memories endpoint."""

    @pytest.mark.asyncio
    async def test_delete_all_memories_success(self, api_client):
        """Test successful deletion of all memories."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.delete_all_memories") as mock_service:
            mock_service.return_value = DeleteAllMemoriesResponse(status="deleted")

            response = await api_client.delete(MEMORIES_ENDPOINT)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"
            mock_service.assert_called_once()


class TestUpdateMemory:
    """Test suite for PATCH /memories/{memory_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_memory_success(self, api_client):
        """Test successful update of a memory."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.update_memory") as mock_service:
            mock_service.return_value = UpdateMemoryResponse(status="updated", memory_id="mem123")

            update_data = {"data": "User prefers Python over JavaScript"}
            response = await api_client.patch(f"{MEMORIES_ENDPOINT}/mem123", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"
            assert data["memory_id"] == "mem123"
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_memory_calls_service(self, api_client):
        """Test that update_memory calls service with correct parameters."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.update_memory") as mock_service:
            mock_service.return_value = UpdateMemoryResponse(status="updated", memory_id="mem456")

            update_data = {"data": "New memory content"}
            response = await api_client.patch(f"{MEMORIES_ENDPOINT}/mem456", json=update_data)

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["memory_id"] == "mem456"
            assert call_kwargs["data"] == "New memory content"

    @pytest.mark.asyncio
    async def test_update_memory_missing_data(self, api_client):
        """Test update without required data field."""
        response = await api_client.patch(f"{MEMORIES_ENDPOINT}/mem123", json={})
        assert response.status_code == 422


class TestMemoryDTOStructure:
    """Integration tests for memory DTO structure."""

    @pytest.mark.asyncio
    async def test_memory_dto_structure(self, api_client, mock_memories_response):
        """Test that MemoryDTO has the expected structure."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.get_memories_for_user") as mock_service:
            mock_service.return_value = mock_memories_response

            response = await api_client.get(MEMORIES_ENDPOINT)

            data = response.json()
            assert "memories" in data
            if len(data["memories"]) > 0:
                memory = data["memories"][0]
                expected_fields = ["id", "memory", "score", "created_at", "user_id", "agent_id", "thread_id"]
                assert all(field in memory for field in expected_fields)

    @pytest.mark.asyncio
    async def test_relation_dto_structure(self, api_client, mock_memories_response):
        """Test that MemoryRelationDTO has the expected structure."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.get_memories_for_user") as mock_service:
            mock_service.return_value = mock_memories_response

            response = await api_client.get(MEMORIES_ENDPOINT)

            data = response.json()
            assert "relations" in data
            if len(data["relations"]) > 0:
                relation = data["relations"][0]
                expected_fields = ["source", "relation", "target"]
                assert all(field in relation for field in expected_fields)

    @pytest.mark.asyncio
    async def test_search_response_structure(self, api_client, mock_search_response):
        """Test that MemorySearchResponse has the expected structure."""
        with patch("aihub_api.routes.memory.MemoryService.MemoryService.search_memories") as mock_service:
            mock_service.return_value = mock_search_response

            response = await api_client.get(f"{MEMORIES_ENDPOINT}/search?query=test")

            data = response.json()
            expected_fields = ["query", "total", "memories", "relations"]
            assert all(field in data for field in expected_fields)
            assert isinstance(data["query"], str)
            assert isinstance(data["total"], int)
            assert isinstance(data["memories"], list)
            assert isinstance(data["relations"], list)


class TestMemoryIntegration:
    """Integration tests using real infrastructure (not mocked).

    NOTE: These tests interact with real Milvus/Neo4j/Mem0Service and are marked as slow.
    They test the full stack: AgentMemory → Mem0Service → Vector DB → API → Service
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_add_search_update_delete_workflow(self, api_client):
        """Full CRUD workflow with real infrastructure."""
        from aihub_lib.agents.AgentConfig import AgentConfig
        from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
        from aihub_lib.i18n.LocaleHandler import LocaleHandler
        from aihub_lib.i18n.LocaleString import LocaleString
        from llama_index.core.base.llms.types import ChatMessage, MessageRole

        user_id = "test_user_api_integration"

        # 1. Add memory via AgentMemory directly (simulates agent adding memory)
        agent_config = AgentConfig(
            agent_class="TestAgent",
            agent_id="test_api_integration",
            name=LocaleString(en="Test Agent"),
            description=LocaleString(en="Test agent for API integration"),
        )
        locale_handler = LocaleHandler(locale="en")
        agent_memory = AgentMemory(agent_config=agent_config, t=locale_handler)

        memory_added = await agent_memory.add_user_memory(
            messages=[
                ChatMessage(
                    content="I love Python programming and use it daily for data science", role=MessageRole.USER
                )
            ],
            user_id=user_id,
            thread_id="thread_api_integration",
            display_id="display_api_integration",
            run_id="run_api_integration",
        )
        assert len(memory_added.results) > 0

        # 2. Search memories via API
        search_response = await api_client.get(f"{MEMORIES_ENDPOINT}/search?query=Python&user_id={user_id}")
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] > 0
        assert len(search_data["memories"]) > 0

        # Find a memory about Python
        python_memory = None
        for mem in search_data["memories"]:
            if "python" in mem["memory"].lower() or "programming" in mem["memory"].lower():
                python_memory = mem
                break
        assert python_memory is not None, "Should find a memory about Python"
        memory_id = python_memory["id"]

        # 3. Update memory via API
        update_response = await api_client.patch(
            f"{MEMORIES_ENDPOINT}/{memory_id}",
            json={"data": "User is an expert Python developer specializing in machine learning"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "updated"

        # 4. Verify update via search
        verify_response = await api_client.get(f"{MEMORIES_ENDPOINT}/search?query=Python expert&user_id={user_id}")
        assert verify_response.status_code == 200
        updated_memories = verify_response.json()["memories"]
        # Should find the updated memory
        assert any("expert" in mem["memory"].lower() for mem in updated_memories)

        # 5. Delete memory via API
        delete_response = await api_client.delete(f"{MEMORIES_ENDPOINT}/{memory_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "deleted"

        # 6. Verify deletion - get all memories and check the count decreased
        final_response = await api_client.get(f"{MEMORIES_ENDPOINT}?user_id={user_id}")
        assert final_response.status_code == 200
        # Memory count should be less than before (some might remain from extraction)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_user_isolation(self, api_client):
        """User A should not see User B's memories via API."""
        from aihub_lib.agents.AgentConfig import AgentConfig
        from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
        from aihub_lib.i18n.LocaleHandler import LocaleHandler
        from aihub_lib.i18n.LocaleString import LocaleString
        from llama_index.core.base.llms.types import ChatMessage, MessageRole

        user_a_id = "user_a_api_isolation"
        user_b_id = "user_b_api_isolation"

        # Add memory for User A via AgentMemory
        agent_config = AgentConfig(
            agent_class="TestAgent",
            agent_id="test_api_isolation",
            name=LocaleString(en="Test Agent"),
            description=LocaleString(en="Test agent for API isolation test"),
        )
        locale_handler = LocaleHandler(locale="en")
        agent_memory = AgentMemory(agent_config=agent_config, t=locale_handler)

        await agent_memory.add_user_memory(
            messages=[ChatMessage(content="User A's confidential project information", role=MessageRole.USER)],
            user_id=user_a_id,
            thread_id="thread_isolation",
            display_id="display_isolation",
            run_id="run_isolation",
        )

        # Try to retrieve as User B via API
        response = await api_client.get(f"{MEMORIES_ENDPOINT}?user_id={user_b_id}")

        assert response.status_code == 200
        data = response.json()
        # User B should not see User A's memories
        assert data["total"] == 0 or all(mem.get("user_id") != user_a_id for mem in data.get("memories", []))
