"""
Unit tests for PatchedAsyncMemory to verify metadata preservation during updates.
"""

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from aihub_lib.infrastructure.mem0.PatchedAsyncMemory import PatchedAsyncMemory


@pytest.fixture
def mock_config():
    """Mock MemoryConfig for testing."""
    return MagicMock()


@pytest.fixture
def mock_vector_store():
    """Mock vector store that returns data with underscore-prefixed metadata."""
    mock_store = MagicMock()

    # Mock the get() method to return a memory with all metadata fields
    mock_memory = MagicMock()
    mock_memory.payload = {
        "data": "Original memory content",
        "hash": "original_hash",
        "created_at": "2024-01-01T00:00:00-08:00",
        "updated_at": "2024-01-01T00:00:00-08:00",
        "user_id": "owner_123",
        "_type": "user_memory",
        "_user_id": "test_user_123",
        "_agent_id": "test_agent_456",
        "_thread_id": "test_thread_789",
        "_display_id": "test_display_abc",
        "_run_id": "test_run_def",
        "_tenant_id": "test_org",
        "_tenant_namespace": "test_namespace",
    }
    mock_store.get.return_value = mock_memory

    # Mock update() to capture what payload is being passed
    mock_store.update = MagicMock()

    return mock_store


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model."""
    mock_model = MagicMock()
    mock_model.embed.return_value = [0.1] * 1536  # Mock embedding vector
    return mock_model


@pytest.fixture
def mock_db():
    """Mock database."""
    return MagicMock()


@pytest.mark.asyncio
async def test_update_memory_preserves_custom_metadata(mock_config, mock_vector_store, mock_embedding_model, mock_db):
    """
    Test that _update_memory preserves ALL custom metadata fields,
    especially underscore-prefixed ones like _thread_id, _user_id, etc.
    """
    # Create PatchedAsyncMemory instance with mocked dependencies
    with patch("aihub_lib.infrastructure.mem0.PatchedAsyncMemory.AsyncMemory.__init__", return_value=None):
        memory = PatchedAsyncMemory(config=mock_config)
        memory.vector_store = mock_vector_store
        memory.embedding_model = mock_embedding_model
        memory.db = mock_db

    # Call _update_memory
    memory_id = "test_memory_123"
    new_data = "Updated memory content"
    existing_embeddings = {new_data: [0.2] * 1536}

    await memory._update_memory(
        memory_id=memory_id,
        data=new_data,
        existing_embeddings=existing_embeddings,
        metadata=None,  # This is what AsyncMemory.update() passes
    )

    # Verify vector_store.update was called
    assert mock_vector_store.update.called, "vector_store.update should have been called"

    # Get the actual payload that was passed to vector_store.update
    call_args = mock_vector_store.update.call_args
    assert call_args is not None, "vector_store.update should have been called with arguments"

    # Extract the payload argument
    _, kwargs = call_args
    actual_payload = kwargs.get("payload")

    assert actual_payload is not None, "payload should be passed to vector_store.update"

    # Verify that ALL underscore-prefixed fields are preserved
    expected_underscore_fields = {
        "_type": "user_memory",
        "_user_id": "test_user_123",
        "_agent_id": "test_agent_456",
        "_thread_id": "test_thread_789",
        "_display_id": "test_display_abc",
        "_run_id": "test_run_def",
        "_tenant_id": "test_org",
        "_tenant_namespace": "test_namespace",
    }

    for field_name, expected_value in expected_underscore_fields.items():
        assert field_name in actual_payload, f"Underscore field '{field_name}' should be preserved"
        assert actual_payload[field_name] == expected_value, (
            f"Underscore field '{field_name}' should have original value '{expected_value}', "
            f"got '{actual_payload.get(field_name)}'"
        )

    # Verify that standard fields are updated correctly
    assert actual_payload["data"] == new_data, "data should be updated"
    assert actual_payload["hash"] == hashlib.md5(new_data.encode()).hexdigest(), "hash should be updated"
    assert actual_payload["created_at"] == "2024-01-01T00:00:00-08:00", "created_at should be preserved"
    assert "updated_at" in actual_payload, "updated_at should be set"

    # Verify that non-underscore fields are also preserved
    assert actual_payload["user_id"] == "owner_123", "user_id should be preserved"

    # Verify db.add_history was called
    assert mock_db.add_history.called, "db.add_history should have been called"


@pytest.mark.asyncio
async def test_update_memory_with_metadata_parameter(mock_config, mock_vector_store, mock_embedding_model, mock_db):
    """
    Test that when metadata parameter is provided, it's merged with existing metadata
    without losing underscore-prefixed fields.
    """
    # Create PatchedAsyncMemory instance with mocked dependencies
    with patch("aihub_lib.infrastructure.mem0.PatchedAsyncMemory.AsyncMemory.__init__", return_value=None):
        memory = PatchedAsyncMemory(config=mock_config)
        memory.vector_store = mock_vector_store
        memory.embedding_model = mock_embedding_model
        memory.db = mock_db

    # Call _update_memory with additional metadata
    memory_id = "test_memory_123"
    new_data = "Updated memory content"
    existing_embeddings = {new_data: [0.2] * 1536}
    additional_metadata = {
        "custom_field": "custom_value",
    }

    await memory._update_memory(
        memory_id=memory_id, data=new_data, existing_embeddings=existing_embeddings, metadata=additional_metadata
    )

    # Get the actual payload
    _, kwargs = mock_vector_store.update.call_args
    actual_payload = kwargs.get("payload")

    # Verify underscore fields are still preserved
    assert actual_payload["_thread_id"] == "test_thread_789", (
        "Underscore fields should be preserved even when metadata is provided"
    )

    # Verify new metadata is added
    assert actual_payload["custom_field"] == "custom_value", "New metadata should be added"


@pytest.mark.asyncio
async def test_update_memory_generates_new_embeddings_when_not_cached(
    mock_config, mock_vector_store, mock_embedding_model, mock_db
):
    """
    Test that new embeddings are generated when not found in existing_embeddings cache.
    """
    # Create PatchedAsyncMemory instance with mocked dependencies
    with patch("aihub_lib.infrastructure.mem0.PatchedAsyncMemory.AsyncMemory.__init__", return_value=None):
        memory = PatchedAsyncMemory(config=mock_config)
        memory.vector_store = mock_vector_store
        memory.embedding_model = mock_embedding_model
        memory.db = mock_db

    # Call _update_memory with empty existing_embeddings (not cached)
    memory_id = "test_memory_123"
    new_data = "Updated memory content"
    existing_embeddings = {}  # Empty cache

    await memory._update_memory(
        memory_id=memory_id, data=new_data, existing_embeddings=existing_embeddings, metadata=None
    )

    # Verify embedding_model.embed was called
    assert mock_embedding_model.embed.called, "embedding_model.embed should be called when embeddings not cached"

    # Verify underscore fields are still preserved
    _, kwargs = mock_vector_store.update.call_args
    actual_payload = kwargs.get("payload")
    assert actual_payload["_thread_id"] == "test_thread_789", "Underscore fields should be preserved"
