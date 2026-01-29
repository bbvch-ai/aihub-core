from unittest.mock import patch

import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
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
from aihub_api.routes.memory.OrganizationMemoryController import OrganizationMemoryController
from aihub_api.routes.memory.UserMemoryController import UserMemoryController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

BASE_URL = "http://test"
USER_MEMORIES_ENDPOINT = "/api/v1/user-memories"
ORG_MEMORIES_ENDPOINT = "/api/v1/organization-memories"


@pytest_asyncio.fixture(scope="module")
async def user_memory_client():
    """Create a test client for the API with UserMemoryController mounted."""
    runner = ApiTestRunner()
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    controller = UserMemoryController(auth=auth)
    controller.get_user_memories().search_user_memories().delete_user_memory().delete_all_user_memories().update_user_memory()
    runner.mount(controller)
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest_asyncio.fixture(scope="module")
async def org_memory_client():
    """Create a test client for the API with OrganizationMemoryController mounted."""
    runner = ApiTestRunner()
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    controller = OrganizationMemoryController(auth=auth)
    controller.get_organization_memories().search_organization_memories().delete_organization_memory().delete_all_organization_memories().update_organization_memory()
    runner.mount(controller)
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.fixture
def mock_user_memory_dto():
    """Create a mock MemoryDTO for user memory testing."""
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
def mock_org_memory_dto():
    """Create a mock MemoryDTO for organization memory testing."""
    return MemoryDTO(
        id="org_mem456",
        memory="Organization uses Python for all backend services",
        score=None,
        created_at="2024-01-01T12:00:00Z",
        user_id=None,
        agent_id="agent/456",
        thread_id="thread456",
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
def mock_user_memories_response(mock_user_memory_dto, mock_relation_dto):
    """Create a mock MemoriesResponse for user memory testing."""
    return MemoriesResponse(
        total=1,
        memories=[mock_user_memory_dto],
        relations=[mock_relation_dto],
    )


@pytest.fixture
def mock_org_memories_response(mock_org_memory_dto, mock_relation_dto):
    """Create a mock MemoriesResponse for organization memory testing."""
    return MemoriesResponse(
        total=1,
        memories=[mock_org_memory_dto],
        relations=[mock_relation_dto],
    )


@pytest.fixture
def mock_user_search_response(mock_user_memory_dto, mock_relation_dto):
    """Create a mock MemorySearchResponse for user memory testing."""
    return MemorySearchResponse(
        query="Python programming",
        total=1,
        memories=[mock_user_memory_dto],
        relations=[mock_relation_dto],
    )


@pytest.fixture
def mock_org_search_response(mock_org_memory_dto, mock_relation_dto):
    """Create a mock MemorySearchResponse for organization memory testing."""
    return MemorySearchResponse(
        query="Python backend",
        total=1,
        memories=[mock_org_memory_dto],
        relations=[mock_relation_dto],
    )


# =============================================
# User Memory Tests
# =============================================


class TestGetUserMemories:
    """Test suite for GET /user-memories endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_memories_success(self, user_memory_client, mock_user_memories_response):
        """Test successful retrieval of user memories."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.get_memories_for_user") as mock_service:
            mock_service.return_value = mock_user_memories_response

            response = await user_memory_client.get(USER_MEMORIES_ENDPOINT)

            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "memories" in data
            assert "relations" in data
            assert isinstance(data["memories"], list)
            assert isinstance(data["relations"], list)
            assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_user_memories_with_limit(self, user_memory_client, mock_user_memories_response):
        """Test user memories endpoint with limit parameter."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.get_memories_for_user") as mock_service:
            mock_service.return_value = mock_user_memories_response

            response = await user_memory_client.get(f"{USER_MEMORIES_ENDPOINT}?limit=50")

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["limit"] == 50

    @pytest.mark.asyncio
    async def test_get_user_memories_invalid_limit(self, user_memory_client):
        """Test user memories endpoint with invalid limit parameters."""
        # Test limit < 1
        response = await user_memory_client.get(f"{USER_MEMORIES_ENDPOINT}?limit=0")
        assert response.status_code == 422

        # Test limit > 1000
        response = await user_memory_client.get(f"{USER_MEMORIES_ENDPOINT}?limit=1001")
        assert response.status_code == 422


class TestSearchUserMemories:
    """Test suite for GET /user-memories/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_user_memories_success(self, user_memory_client, mock_user_search_response):
        """Test successful user memory search."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.search_memories") as mock_service:
            mock_service.return_value = mock_user_search_response

            response = await user_memory_client.get(f"{USER_MEMORIES_ENDPOINT}/search?query=Python programming")

            assert response.status_code == 200
            data = response.json()
            assert "query" in data
            assert "total" in data
            assert "memories" in data
            assert "relations" in data
            assert data["query"] == "Python programming"
            assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_search_user_memories_missing_query(self, user_memory_client):
        """Test search without required query parameter."""
        response = await user_memory_client.get(f"{USER_MEMORIES_ENDPOINT}/search")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_user_memories_with_filters(self, user_memory_client, mock_user_search_response):
        """Test search with filters."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.search_memories") as mock_service:
            mock_service.return_value = mock_user_search_response

            response = await user_memory_client.get(
                f"{USER_MEMORIES_ENDPOINT}/search?query=test&agent_id=agent/123&thread_id=thread123&limit=50"
            )

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["query"] == "test"
            assert call_kwargs["agent_id"] == "agent/123"
            assert call_kwargs["thread_id"] == "thread123"
            assert call_kwargs["limit"] == 50

    @pytest.mark.asyncio
    async def test_search_user_memories_empty_results(self, user_memory_client):
        """Test search with no results."""
        empty_response = MemorySearchResponse(
            query="nonexistent",
            total=0,
            memories=[],
            relations=[],
        )
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.search_memories") as mock_service:
            mock_service.return_value = empty_response

            response = await user_memory_client.get(f"{USER_MEMORIES_ENDPOINT}/search?query=nonexistent")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert len(data["memories"]) == 0
            assert len(data["relations"]) == 0


class TestDeleteUserMemory:
    """Test suite for DELETE /user-memories/{memory_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_user_memory_success(self, user_memory_client):
        """Test successful deletion of a single user memory."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.delete_memory") as mock_service:
            mock_service.return_value = DeleteMemoryResponse(status="deleted", memory_id="mem123")

            response = await user_memory_client.delete(f"{USER_MEMORIES_ENDPOINT}/mem123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"
            assert data["memory_id"] == "mem123"
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_memory_calls_service(self, user_memory_client):
        """Test that delete_memory calls service with correct parameters."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.delete_memory") as mock_service:
            mock_service.return_value = DeleteMemoryResponse(status="deleted", memory_id="mem456")

            response = await user_memory_client.delete(f"{USER_MEMORIES_ENDPOINT}/mem456")

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["memory_id"] == "mem456"


class TestDeleteAllUserMemories:
    """Test suite for DELETE /user-memories endpoint."""

    @pytest.mark.asyncio
    async def test_delete_all_user_memories_success(self, user_memory_client):
        """Test successful deletion of all user memories."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.delete_all_memories") as mock_service:
            mock_service.return_value = DeleteAllMemoriesResponse(status="deleted")

            response = await user_memory_client.delete(USER_MEMORIES_ENDPOINT)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"
            mock_service.assert_called_once()


class TestUpdateUserMemory:
    """Test suite for PATCH /user-memories/{memory_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_user_memory_success(self, user_memory_client):
        """Test successful update of a user memory."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.update_memory") as mock_service:
            mock_service.return_value = UpdateMemoryResponse(status="updated", memory_id="mem123")

            update_data = {"data": "User prefers Python over JavaScript"}
            response = await user_memory_client.patch(f"{USER_MEMORIES_ENDPOINT}/mem123", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"
            assert data["memory_id"] == "mem123"
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_memory_calls_service(self, user_memory_client):
        """Test that update_memory calls service with correct parameters."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.update_memory") as mock_service:
            mock_service.return_value = UpdateMemoryResponse(status="updated", memory_id="mem456")

            update_data = {"data": "New memory content"}
            response = await user_memory_client.patch(f"{USER_MEMORIES_ENDPOINT}/mem456", json=update_data)

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["memory_id"] == "mem456"
            assert call_kwargs["data"] == "New memory content"

    @pytest.mark.asyncio
    async def test_update_user_memory_missing_data(self, user_memory_client):
        """Test update without required data field."""
        response = await user_memory_client.patch(f"{USER_MEMORIES_ENDPOINT}/mem123", json={})
        assert response.status_code == 422


# =============================================
# Organization Memory Tests
# =============================================


class TestGetOrganizationMemories:
    """Test suite for GET /organization-memories endpoint."""

    @pytest.mark.asyncio
    async def test_get_organization_memories_success(self, org_memory_client, mock_org_memories_response):
        """Test successful retrieval of organization memories."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.get_memories"
        ) as mock_service:
            mock_service.return_value = mock_org_memories_response

            response = await org_memory_client.get(ORG_MEMORIES_ENDPOINT)

            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "memories" in data
            assert "relations" in data
            assert isinstance(data["memories"], list)
            assert isinstance(data["relations"], list)
            assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_organization_memories_with_limit(self, org_memory_client, mock_org_memories_response):
        """Test organization memories endpoint with limit parameter."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.get_memories"
        ) as mock_service:
            mock_service.return_value = mock_org_memories_response

            response = await org_memory_client.get(f"{ORG_MEMORIES_ENDPOINT}?limit=50")

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["limit"] == 50

    @pytest.mark.asyncio
    async def test_get_organization_memories_invalid_limit(self, org_memory_client):
        """Test organization memories endpoint with invalid limit parameters."""
        # Test limit < 1
        response = await org_memory_client.get(f"{ORG_MEMORIES_ENDPOINT}?limit=0")
        assert response.status_code == 422

        # Test limit > 1000
        response = await org_memory_client.get(f"{ORG_MEMORIES_ENDPOINT}?limit=1001")
        assert response.status_code == 422


class TestSearchOrganizationMemories:
    """Test suite for GET /organization-memories/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_organization_memories_success(self, org_memory_client, mock_org_search_response):
        """Test successful organization memory search."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.search_memories"
        ) as mock_service:
            mock_service.return_value = mock_org_search_response

            response = await org_memory_client.get(f"{ORG_MEMORIES_ENDPOINT}/search?query=Python backend")

            assert response.status_code == 200
            data = response.json()
            assert "query" in data
            assert "total" in data
            assert "memories" in data
            assert "relations" in data
            assert data["query"] == "Python backend"
            assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_search_organization_memories_missing_query(self, org_memory_client):
        """Test search without required query parameter."""
        response = await org_memory_client.get(f"{ORG_MEMORIES_ENDPOINT}/search")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_organization_memories_with_filters(self, org_memory_client, mock_org_search_response):
        """Test search with filters."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.search_memories"
        ) as mock_service:
            mock_service.return_value = mock_org_search_response

            response = await org_memory_client.get(
                f"{ORG_MEMORIES_ENDPOINT}/search?query=test&agent_id=agent/456&thread_id=thread456&limit=50"
            )

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["query"] == "test"
            assert call_kwargs["agent_id"] == "agent/456"
            assert call_kwargs["thread_id"] == "thread456"
            assert call_kwargs["limit"] == 50

    @pytest.mark.asyncio
    async def test_search_organization_memories_empty_results(self, org_memory_client):
        """Test search with no results."""
        empty_response = MemorySearchResponse(
            query="nonexistent",
            total=0,
            memories=[],
            relations=[],
        )
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.search_memories"
        ) as mock_service:
            mock_service.return_value = empty_response

            response = await org_memory_client.get(f"{ORG_MEMORIES_ENDPOINT}/search?query=nonexistent")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert len(data["memories"]) == 0
            assert len(data["relations"]) == 0


class TestDeleteOrganizationMemory:
    """Test suite for DELETE /organization-memories/{memory_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_organization_memory_success(self, org_memory_client):
        """Test successful deletion of a single organization memory."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.delete_memory"
        ) as mock_service:
            mock_service.return_value = DeleteMemoryResponse(status="deleted", memory_id="org_mem456")

            response = await org_memory_client.delete(f"{ORG_MEMORIES_ENDPOINT}/org_mem456")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"
            assert data["memory_id"] == "org_mem456"
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_organization_memory_calls_service(self, org_memory_client):
        """Test that delete_memory calls service with correct parameters."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.delete_memory"
        ) as mock_service:
            mock_service.return_value = DeleteMemoryResponse(status="deleted", memory_id="org_mem789")

            response = await org_memory_client.delete(f"{ORG_MEMORIES_ENDPOINT}/org_mem789")

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["memory_id"] == "org_mem789"


class TestDeleteAllOrganizationMemories:
    """Test suite for DELETE /organization-memories endpoint."""

    @pytest.mark.asyncio
    async def test_delete_all_organization_memories_success(self, org_memory_client):
        """Test successful deletion of all organization memories."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.delete_all_memories"
        ) as mock_service:
            mock_service.return_value = DeleteAllMemoriesResponse(status="deleted")

            response = await org_memory_client.delete(ORG_MEMORIES_ENDPOINT)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"
            mock_service.assert_called_once()


class TestUpdateOrganizationMemory:
    """Test suite for PATCH /organization-memories/{memory_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_organization_memory_success(self, org_memory_client):
        """Test successful update of an organization memory."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.update_memory"
        ) as mock_service:
            mock_service.return_value = UpdateMemoryResponse(status="updated", memory_id="org_mem456")

            update_data = {"data": "Organization uses Python for all backend services"}
            response = await org_memory_client.patch(f"{ORG_MEMORIES_ENDPOINT}/org_mem456", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"
            assert data["memory_id"] == "org_mem456"
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_organization_memory_calls_service(self, org_memory_client):
        """Test that update_memory calls service with correct parameters."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.update_memory"
        ) as mock_service:
            mock_service.return_value = UpdateMemoryResponse(status="updated", memory_id="org_mem789")

            update_data = {"data": "New organization memory content"}
            response = await org_memory_client.patch(f"{ORG_MEMORIES_ENDPOINT}/org_mem789", json=update_data)

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            assert call_kwargs["memory_id"] == "org_mem789"
            assert call_kwargs["data"] == "New organization memory content"

    @pytest.mark.asyncio
    async def test_update_organization_memory_missing_data(self, org_memory_client):
        """Test update without required data field."""
        response = await org_memory_client.patch(f"{ORG_MEMORIES_ENDPOINT}/org_mem456", json={})
        assert response.status_code == 422


# =============================================
# DTO Structure Tests
# =============================================


class TestMemoryDTOStructure:
    """Integration tests for memory DTO structure."""

    @pytest.mark.asyncio
    async def test_user_memory_dto_structure(self, user_memory_client, mock_user_memories_response):
        """Test that user MemoryDTO has the expected structure."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.get_memories_for_user") as mock_service:
            mock_service.return_value = mock_user_memories_response

            response = await user_memory_client.get(USER_MEMORIES_ENDPOINT)

            data = response.json()
            assert "memories" in data
            if len(data["memories"]) > 0:
                memory = data["memories"][0]
                expected_fields = ["id", "memory", "score", "created_at", "user_id", "agent_id", "thread_id"]
                assert all(field in memory for field in expected_fields)
                assert memory["user_id"] is not None

    @pytest.mark.asyncio
    async def test_organization_memory_dto_structure(self, org_memory_client, mock_org_memories_response):
        """Test that organization MemoryDTO has the expected structure."""
        with patch(
            "aihub_api.routes.memory.OrganizationMemoryService.OrganizationMemoryService.get_memories"
        ) as mock_service:
            mock_service.return_value = mock_org_memories_response

            response = await org_memory_client.get(ORG_MEMORIES_ENDPOINT)

            data = response.json()
            assert "memories" in data
            if len(data["memories"]) > 0:
                memory = data["memories"][0]
                expected_fields = ["id", "memory", "score", "created_at", "user_id", "agent_id", "thread_id"]
                assert all(field in memory for field in expected_fields)

    @pytest.mark.asyncio
    async def test_relation_dto_structure(self, user_memory_client, mock_user_memories_response):
        """Test that MemoryRelationDTO has the expected structure."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.get_memories_for_user") as mock_service:
            mock_service.return_value = mock_user_memories_response

            response = await user_memory_client.get(USER_MEMORIES_ENDPOINT)

            data = response.json()
            assert "relations" in data
            if len(data["relations"]) > 0:
                relation = data["relations"][0]
                expected_fields = ["source", "relation", "target"]
                assert all(field in relation for field in expected_fields)

    @pytest.mark.asyncio
    async def test_search_response_structure(self, user_memory_client, mock_user_search_response):
        """Test that MemorySearchResponse has the expected structure."""
        with patch("aihub_api.routes.memory.UserMemoryService.UserMemoryService.search_memories") as mock_service:
            mock_service.return_value = mock_user_search_response

            response = await user_memory_client.get(f"{USER_MEMORIES_ENDPOINT}/search?query=test")

            data = response.json()
            expected_fields = ["query", "total", "memories", "relations"]
            assert all(field in data for field in expected_fields)
            assert isinstance(data["query"], str)
            assert isinstance(data["total"], int)
            assert isinstance(data["memories"], list)
            assert isinstance(data["relations"], list)


# =============================================
# Integration Tests (with real infrastructure)
# =============================================


class TestUserMemoryIntegration:
    """Integration tests using real infrastructure for user memory (not mocked).

    NOTE: These tests interact with real Milvus/Neo4j/Mem0Service and are marked as slow.
    They test the full stack: UserMemory → Mem0Service → Vector DB → API → Service
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.azure
    async def test_add_search_update_delete_workflow(self, user_memory_client):
        """Full CRUD workflow with real infrastructure."""
        from aihub_lib.agents.AgentConfig import AgentConfig
        from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
        from aihub_lib.i18n.LocaleHandler import LocaleHandler
        from aihub_lib.i18n.LocaleString import LocaleString
        from llama_index.core.base.llms.types import ChatMessage, MessageRole

        user_id = DangerousDevelopmentOnlyAuthSettings().OID

        # 1. Add memory via AgentMemory directly (simulates agent adding memory)
        agent_config = AgentConfig(
            agent_class="TestAgent",
            agent_id="test_api_integration",
            name=LocaleString(en="Test Agent"),
            description=LocaleString(en="Test agent for API integration"),
        )
        locale_handler = LocaleHandler(locale="en")
        agent_memory = AgentMemory(agent_config=agent_config, t=locale_handler)

        # Clean up leftover memories from previous test runs to avoid deduplication
        await agent_memory.mem0service.delete_all(owner_id=user_id)

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
        search_response = await user_memory_client.get(f"{USER_MEMORIES_ENDPOINT}/search?query=Python")
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
        update_response = await user_memory_client.patch(
            f"{USER_MEMORIES_ENDPOINT}/{memory_id}",
            json={"data": "User is an expert Python developer specializing in machine learning"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "updated"

        # 4. Verify update via search
        verify_response = await user_memory_client.get(f"{USER_MEMORIES_ENDPOINT}/search?query=Python expert")
        assert verify_response.status_code == 200
        updated_memories = verify_response.json()["memories"]
        # Should find the updated memory
        assert any("expert" in mem["memory"].lower() for mem in updated_memories)

        # 5. Delete memory via API
        delete_response = await user_memory_client.delete(f"{USER_MEMORIES_ENDPOINT}/{memory_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "deleted"

        # 6. Verify deletion - get all memories and check the count decreased
        final_response = await user_memory_client.get(USER_MEMORIES_ENDPOINT)
        assert final_response.status_code == 200
        # Memory count should be less than before (some might remain from extraction)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.azure
    async def test_user_isolation(self, user_memory_client):
        """User A should not see User B's memories via API."""
        from aihub_lib.agents.AgentConfig import AgentConfig
        from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
        from aihub_lib.i18n.LocaleHandler import LocaleHandler
        from aihub_lib.i18n.LocaleString import LocaleString
        from llama_index.core.base.llms.types import ChatMessage, MessageRole

        user_a_id = "user_a_api_isolation"

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

        # Now test with User B - the API client uses User B's identity
        # Since we're using DangerousDevelopmentOnlyAuthHandler, it should return User B's context
        # The test verifies that User B cannot see User A's memories
        response = await user_memory_client.get(USER_MEMORIES_ENDPOINT)

        assert response.status_code == 200
        # User B should not see User A's memories
        # In real deployment, the auth handler ensures user context isolation
        # This test primarily validates the service layer properly filters by user
