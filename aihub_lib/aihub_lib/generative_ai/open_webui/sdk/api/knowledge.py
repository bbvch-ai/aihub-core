from typing import Any, Dict, List, Optional, Union

from ..client import BaseClient
from ..models.knowledge import (
    KnowledgeAccessControl,
    KnowledgeAccessControlPermissions,
    KnowledgeData,
    KnowledgeFileIdForm,
    KnowledgeFilesResponse,
    KnowledgeForm,
    KnowledgeResponse,
    KnowledgeUserResponse,
)


class KnowledgeClient(BaseClient):
    """
    Client for interacting with OpenWebUI knowledge base API endpoints.

    Knowledge bases are collections of files used for context retrieval
    during chat interactions. This client provides methods for creating,
    managing, and using knowledge bases.

    Example:
        ```python
        from sdk import OpenWebuiClient
        import asyncio

        async def manage_knowledge():
            client = OpenWebuiClient(token="your-token")

            # Create a new knowledge base
            kb = await client.knowledge.create_knowledge(
                name="Project Documentation",
                description="All documentation for our project"
            )

            # Add a file to the knowledge base
            await client.knowledge.add_file_to_knowledge(
                knowledge_id=kb.id,
                file_id="file123"
            )

            # Get all knowledge bases
            all_kb = await client.knowledge.get_knowledge_bases()

        asyncio.run(manage_knowledge())
        ```
    """

    async def get_knowledge_bases(self) -> List[KnowledgeUserResponse]:
        """Get all knowledge bases the user has read access to"""
        response = await self.get("/token/v1/knowledge/")
        return [KnowledgeUserResponse.model_validate(kb) for kb in response.json()]

    async def get_writable_knowledge_bases(self) -> List[KnowledgeUserResponse]:
        """Get all knowledge bases the user has write access to"""
        response = await self.get("/token/v1/knowledge/list")
        return [KnowledgeUserResponse.model_validate(kb) for kb in response.json()]

    async def create_knowledge(
        self,
        name: str,
        description: str,
        file_ids: Optional[List[str]] = None,
        access_control: Optional[Union[KnowledgeAccessControl, Dict[str, Any]]] = None,
    ) -> KnowledgeResponse:
        """Create a new knowledge base"""
        # Prepare the knowledge data - file_ids is the main content
        data = None
        if file_ids is not None:
            data = KnowledgeData(file_ids=file_ids)

        # Create the form data object
        form_data = KnowledgeForm(
            name=name,
            description=description,
            data=data.model_dump() if data else None,
            access_control=access_control.model_dump() if hasattr(access_control, "model_dump") else access_control,
        )

        response = await self.post("/token/v1/knowledge/create", json_data=form_data.model_dump())
        return KnowledgeResponse.model_validate(response.json())

    async def get_knowledge(self, knowledge_id: str) -> KnowledgeFilesResponse:
        """Get detailed information about a knowledge base by ID"""
        response = await self.get(f"/token/v1/knowledge/{knowledge_id}")
        return KnowledgeFilesResponse.model_validate(response.json())

    async def update_knowledge(
        self,
        knowledge_id: str,
        name: str,
        description: str,
        file_ids: Optional[List[str]] = None,
        access_control: Optional[Union[KnowledgeAccessControl, Dict[str, Any]]] = None,
    ) -> KnowledgeFilesResponse:
        """Update a knowledge base by ID"""
        # Get existing knowledge base to preserve data if file_ids is None
        existing = None
        if file_ids is None:
            try:
                existing = await self.get_knowledge(knowledge_id)
            except Exception:
                pass

        data = None
        if file_ids is not None:
            data = KnowledgeData(file_ids=file_ids)
        elif existing and existing.data:
            # Use existing data from the server
            data = existing.data

        form_data = KnowledgeForm(
            name=name,
            description=description,
            data=data.model_dump() if hasattr(data, "model_dump") else data,
            access_control=access_control.model_dump() if hasattr(access_control, "model_dump") else access_control,
        )

        response = await self.post(f"/token/v1/knowledge/{knowledge_id}/update", json_data=form_data.model_dump())
        return KnowledgeFilesResponse.model_validate(response.json())

    async def add_file_to_knowledge(self, knowledge_id: str, file_id: str) -> KnowledgeFilesResponse:
        """Add a file to a knowledge base"""
        form_data = KnowledgeFileIdForm(file_id=file_id)
        response = await self.post(f"/token/v1/knowledge/{knowledge_id}/file/add", json_data=form_data.model_dump())
        return KnowledgeFilesResponse.model_validate(response.json())

    async def update_file_in_knowledge(self, knowledge_id: str, file_id: str) -> KnowledgeFilesResponse:
        """Update a file in a knowledge base (reprocess the file)"""
        form_data = KnowledgeFileIdForm(file_id=file_id)
        response = await self.post(f"/token/v1/knowledge/{knowledge_id}/file/update", json_data=form_data.model_dump())
        return KnowledgeFilesResponse.model_validate(response.json())

    async def remove_file_from_knowledge(self, knowledge_id: str, file_id: str) -> KnowledgeFilesResponse:
        """Remove a file from a knowledge base"""
        form_data = KnowledgeFileIdForm(file_id=file_id)
        response = await self.post(f"/token/v1/knowledge/{knowledge_id}/file/remove", json_data=form_data.model_dump())
        return KnowledgeFilesResponse.model_validate(response.json())

    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """Delete a knowledge base by ID"""
        response = await self.delete(f"/token/v1/knowledge/{knowledge_id}/delete")
        return response.json()

    async def reset_knowledge(self, knowledge_id: str) -> KnowledgeResponse:
        """Reset a knowledge base (removes all files from the knowledge base)"""
        response = await self.post(f"/token/v1/knowledge/{knowledge_id}/reset")
        return KnowledgeResponse.model_validate(response.json())

    async def add_files_batch(self, knowledge_id: str, file_ids: List[str]) -> KnowledgeFilesResponse:
        """Add multiple files to a knowledge base in a single operation"""
        form_data = [KnowledgeFileIdForm(file_id=file_id) for file_id in file_ids]
        response = await self.post(
            f"/token/v1/knowledge/{knowledge_id}/files/batch/add", json_data=[form.model_dump() for form in form_data]
        )
        return KnowledgeFilesResponse.model_validate(response.json())

    # Helper methods for creating properly typed access control objects

    def create_access_control(
        self,
        read_user_ids: Optional[List[str]] = None,
        read_group_ids: Optional[List[str]] = None,
        write_user_ids: Optional[List[str]] = None,
        write_group_ids: Optional[List[str]] = None,
    ) -> KnowledgeAccessControl:
        """Create a properly structured access control object for knowledge bases"""
        return KnowledgeAccessControl(
            read=KnowledgeAccessControlPermissions(user_ids=read_user_ids or [], group_ids=read_group_ids or []),
            write=KnowledgeAccessControlPermissions(user_ids=write_user_ids or [], group_ids=write_group_ids or []),
        )

    def create_public_access_control(self) -> KnowledgeAccessControl:
        """Create an access control object for a public knowledge base (readable by everyone)"""
        return KnowledgeAccessControl(
            read=KnowledgeAccessControlPermissions(user_ids=[], group_ids=[]),
            write=KnowledgeAccessControlPermissions(user_ids=[], group_ids=[]),
        )

    def create_private_access_control(self) -> KnowledgeAccessControl:
        """Create an access control object for a private knowledge base (readable only by owner)"""
        # In the API, a private access control is represented by {}
        # This will be serialized correctly during the API call
        return KnowledgeAccessControl()
