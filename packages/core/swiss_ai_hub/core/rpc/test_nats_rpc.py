"""Tests for NATS request-reply abstractions (requester, responder, and rpc clients)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from swiss_ai_hub.core.requester.nc_requester import NCRequester
from swiss_ai_hub.core.responder.nc_responder import NCResponder
from swiss_ai_hub.core.rpc.agent_config_client import AgentConfigClient
from swiss_ai_hub.core.rpc.models import (
    FetchAgentConfigRequest,
    FetchAgentConfigResponse,
)


# Test models
class SimpleRequest(BaseModel):
    """Simple request model for testing."""

    message: str


class SimpleResponse(BaseModel):
    """Simple response model for testing."""

    result: str
    success: bool = True


class TestNCRequester:
    """Test cases for NCRequester class."""

    @pytest.fixture
    def mock_nc(self) -> MagicMock:
        """Create a mock NATS client."""
        nc = MagicMock()
        nc.request = AsyncMock()
        return nc

    @pytest.fixture
    def requester(self, mock_nc: MagicMock) -> NCRequester[SimpleRequest, SimpleResponse]:
        """Create a requester instance for testing."""
        return NCRequester(
            name="TestRequester",
            nc=mock_nc,
            response_cls=SimpleResponse,
            default_timeout_ms=1000,
        )

    def test_requester_name_suffix(self, mock_nc: MagicMock) -> None:
        """Test that requester name gets correct suffix."""
        requester = NCRequester(
            name="Test",
            nc=mock_nc,
            response_cls=SimpleResponse,
        )
        assert requester.name == "TestNATSRequester"

        # Already has suffix
        requester2 = NCRequester(
            name="TestNATSRequester",
            nc=mock_nc,
            response_cls=SimpleResponse,
        )
        assert requester2.name == "TestNATSRequester"

    @pytest.mark.asyncio
    async def test_request_success(
        self, requester: NCRequester[SimpleRequest, SimpleResponse], mock_nc: MagicMock
    ) -> None:
        """Test successful request-response cycle."""
        # Setup mock response
        mock_msg = MagicMock()
        mock_msg.data = b'{"result": "hello", "success": true}'
        mock_nc.request.return_value = mock_msg

        # Make request
        with patch("swiss_ai_hub.core.requester.nc_requester.get_tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=None)
            mock_tracer.return_value.start_as_current_span.return_value = mock_span

            response = await requester.request(
                SimpleRequest(message="test"),
                subject="test.subject",
            )

        assert response.result == "hello"
        assert response.success is True
        mock_nc.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_timeout(
        self, requester: NCRequester[SimpleRequest, SimpleResponse], mock_nc: MagicMock
    ) -> None:
        """Test that timeout raises TimeoutError."""
        from nats.errors import TimeoutError as NatsTimeoutError

        mock_nc.request.side_effect = NatsTimeoutError()

        with patch("swiss_ai_hub.core.requester.nc_requester.get_tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=None)
            mock_tracer.return_value.start_as_current_span.return_value = mock_span

            with pytest.raises(TimeoutError, match="timed out"):
                await requester.request(
                    SimpleRequest(message="test"),
                    subject="test.subject",
                )

    @pytest.mark.asyncio
    async def test_request_custom_timeout(
        self, requester: NCRequester[SimpleRequest, SimpleResponse], mock_nc: MagicMock
    ) -> None:
        """Test that custom timeout is passed correctly."""
        mock_msg = MagicMock()
        mock_msg.data = b'{"result": "ok", "success": true}'
        mock_nc.request.return_value = mock_msg

        with patch("swiss_ai_hub.core.requester.nc_requester.get_tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=None)
            mock_tracer.return_value.start_as_current_span.return_value = mock_span

            await requester.request(
                SimpleRequest(message="test"),
                subject="test.subject",
                timeout_ms=3000,
            )

        # Verify timeout was converted to seconds (3000ms = 3.0s)
        call_kwargs = mock_nc.request.call_args[1]
        assert call_kwargs["timeout"] == 3.0


class TestNCResponder:
    """Test cases for NCResponder class."""

    @pytest.fixture
    def mock_nc(self) -> MagicMock:
        """Create a mock NATS client."""
        nc = MagicMock()
        nc.subscribe = AsyncMock()
        return nc

    @pytest.fixture
    def handler(self) -> AsyncMock:
        """Create a mock handler function."""
        return AsyncMock(return_value=SimpleResponse(result="handled"))

    @pytest.fixture
    def responder(self, mock_nc: MagicMock, handler: AsyncMock) -> NCResponder[SimpleRequest, SimpleResponse]:
        """Create a responder instance for testing."""
        return NCResponder(
            name="TestResponder",
            nc=mock_nc,
            subject="test.subject.*",
            request_cls=SimpleRequest,
            handler=handler,
        )

    def test_responder_name_suffix(self, mock_nc: MagicMock, handler: AsyncMock) -> None:
        """Test that responder name gets correct suffix."""
        responder = NCResponder(
            name="Test",
            nc=mock_nc,
            subject="test.*",
            request_cls=SimpleRequest,
            handler=handler,
        )
        assert responder.name == "TestNATSResponder"

    @pytest.mark.asyncio
    async def test_start_subscribes(
        self, responder: NCResponder[SimpleRequest, SimpleResponse], mock_nc: MagicMock
    ) -> None:
        """Test that start() subscribes to the subject."""
        mock_subscription = MagicMock()
        mock_nc.subscribe.return_value = mock_subscription

        await responder.start()

        mock_nc.subscribe.assert_called_once()
        assert responder._subscription == mock_subscription

    @pytest.mark.asyncio
    async def test_stop_unsubscribes(
        self, responder: NCResponder[SimpleRequest, SimpleResponse], mock_nc: MagicMock
    ) -> None:
        """Test that stop() unsubscribes from the subject."""
        mock_subscription = MagicMock()
        mock_subscription.unsubscribe = AsyncMock()
        responder._subscription = mock_subscription

        await responder.stop()

        mock_subscription.unsubscribe.assert_called_once()
        assert responder._subscription is None

    @pytest.mark.asyncio
    async def test_process_request_calls_handler(
        self,
        responder: NCResponder[SimpleRequest, SimpleResponse],
        handler: AsyncMock,
    ) -> None:
        """Test that incoming requests are processed by the handler."""
        # Create mock message
        mock_msg = MagicMock()
        mock_msg.data = b'{"message": "hello"}'
        mock_msg.subject = "test.subject.123"
        mock_msg.headers = {}
        mock_msg.respond = AsyncMock()

        with patch("swiss_ai_hub.core.responder.nc_responder.get_tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=None)
            mock_tracer.return_value.start_as_current_span.return_value = mock_span

            await responder._process_request(mock_msg)

        handler.assert_called_once()
        call_args = handler.call_args[0]
        assert isinstance(call_args[0], SimpleRequest)
        assert call_args[0].message == "hello"
        assert call_args[1] == "test.subject.123"

        # Verify response was sent
        mock_msg.respond.assert_called_once()


class TestAgentConfigClient:
    """Test cases for AgentConfigClient class."""

    @pytest.fixture
    def mock_nc(self) -> MagicMock:
        """Create a mock NATS client."""
        nc = MagicMock()
        nc.request = AsyncMock()
        return nc

    @pytest.fixture
    def client(self, mock_nc: MagicMock) -> AgentConfigClient:
        """Create an AgentConfigClient instance for testing."""
        return AgentConfigClient(nc=mock_nc, timeout_ms=1000)

    @pytest.mark.asyncio
    async def test_fetch_config_success(self, client: AgentConfigClient, mock_nc: MagicMock) -> None:
        """Test successful config fetch."""
        # Setup mock response
        response = FetchAgentConfigResponse(
            agent_class="RAGAgent",
            agent_id="default",
            config={"model": "gpt-4", "temperature": 0.7},
            found=True,
        )
        mock_msg = MagicMock()
        mock_msg.data = response.model_dump_json().encode()
        mock_nc.request.return_value = mock_msg

        with patch("swiss_ai_hub.core.requester.nc_requester.get_tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=None)
            mock_tracer.return_value.start_as_current_span.return_value = mock_span

            config = await client.fetch_config("RAGAgent", "default")

        assert config == {"model": "gpt-4", "temperature": 0.7}

        # Verify correct subject was used
        call_args = mock_nc.request.call_args[0]
        assert call_args[0] == "aihub.rpc.config.agent.RAGAgent.default"

    @pytest.mark.asyncio
    async def test_fetch_config_not_found(self, client: AgentConfigClient, mock_nc: MagicMock) -> None:
        """Test that ValueError is raised when config not found."""
        response = FetchAgentConfigResponse(
            agent_class="RAGAgent",
            agent_id="nonexistent",
            config={},
            found=False,
            error="Agent not found",
        )
        mock_msg = MagicMock()
        mock_msg.data = response.model_dump_json().encode()
        mock_nc.request.return_value = mock_msg

        with patch("swiss_ai_hub.core.requester.nc_requester.get_tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_span.__enter__ = MagicMock(return_value=mock_span)
            mock_span.__exit__ = MagicMock(return_value=None)
            mock_tracer.return_value.start_as_current_span.return_value = mock_span

            with pytest.raises(ValueError, match="Config not found"):
                await client.fetch_config("RAGAgent", "nonexistent")

    def test_subject_pattern(self, client: AgentConfigClient) -> None:
        """Test that subject pattern is correct via topic manager."""
        # The subject is generated by the topic manager
        subject = client._topic_manager.get_agent_config_rpc_subject("TestAgent", "test-1")
        assert subject == "aihub.rpc.config.agent.TestAgent.test-1"


class TestFetchAgentConfigModels:
    """Test cases for FetchAgentConfig request/response models."""

    def test_request_serialization(self) -> None:
        """Test that request model serializes correctly."""
        request = FetchAgentConfigRequest(agent_class="TestAgent", agent_id="test-1")
        data = request.model_dump_json()
        assert "TestAgent" in data
        assert "test-1" in data

    def test_response_serialization(self) -> None:
        """Test that response model serializes correctly."""
        response = FetchAgentConfigResponse(
            agent_class="TestAgent",
            agent_id="test-1",
            config={"key": "value"},
            found=True,
        )
        data = response.model_dump_json()
        assert "TestAgent" in data
        assert "test-1" in data
        assert "key" in data

    def test_response_defaults(self) -> None:
        """Test response model default values."""
        response = FetchAgentConfigResponse(
            agent_class="TestAgent",
            agent_id="test-1",
            config={},
        )
        assert response.found is True
        assert response.error is None

    def test_response_with_error(self) -> None:
        """Test response model with error."""
        response = FetchAgentConfigResponse(
            agent_class="TestAgent",
            agent_id="test-1",
            config={},
            found=False,
            error="Agent not found",
        )
        assert response.found is False
        assert response.error == "Agent not found"
