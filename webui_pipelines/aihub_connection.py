"""
title: AI-Hub Assistants
description: Makes aihub assistants accessible in open webui
required_open_webui_version: 0.6.0
"""

import httpx
import requests
import hashlib
import uuid
import json
from typing import Optional, List, Dict, Any, Generator, AsyncGenerator, Union
from bson import ObjectId
import asyncio
import logging
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

def str_to_object_id(context_id: Optional[str]) -> str:
    if not context_id:
        return str(ObjectId())
    hashed = hashlib.md5(context_id.encode()).digest()[:12]
    return str(ObjectId(hashed))

def hash_string_sha1(input_string):
    static_salt = f"k2oj3dk2*dk2p&29dkjklUdk(3kKldi39djkd?+lfdfdf"
    hash_input = f"{static_salt}{input_string}"
    input_bytes = hash_input.encode("utf-8")
    sha1_hash = hashlib.sha1(input_bytes)
    hex_digest = sha1_hash.hexdigest()
    return hex_digest

def user_header(__user__: dict):
    username = __user__.get("name")
    email = __user__.get("email")

    username_hash = hashlib.sha1(username.encode("utf-8")).hexdigest()
    email_hash = hashlib.sha1(email.encode("utf-8")).hexdigest()

    return {
        "X-OpenWebUI-User-Name": username,
        "X-OpenWebUI-User-Email": email,
        "X-OpenWebUI-User-Name-Hash": username_hash,
        "X-OpenWebUI-User-Email-Hash": email_hash,
    }

def transform_events_to_sources(events: List[Dict]) -> Dict[str, Any]:
    """Transform retriever events into the sources format expected by the UI."""
    result = {
        "type": "chat:completion",
        "data": {
            "sources": []
        }
    }

    # Deduplicate documents by their id
    unique_docs = {}
    for event in events:
        documents = event.get("event", {}).get("documents", [])
        for doc in documents:
            doc_id = doc.get("id")
            if doc_id and doc_id not in unique_docs:
                unique_docs[doc_id] = doc

    # Group documents by their metadata.source
    grouped_docs = {}
    for doc_id, doc in unique_docs.items():
        metadata = doc.get("metadata", {})
        source = metadata.get("source", "Unknown Source")
        if source not in grouped_docs:
            grouped_docs[source] = {"documents": [], "metadata": [], "distances": []}

        # Add document content
        content = doc.get("content", "")
        grouped_docs[source]["documents"].append(content)

        # Create metadata entry
        doc_title = metadata.get("document_title", "Document")
        heading_parts = [metadata.get(h) for h in ["h1", "h2", "h3"] if metadata.get(h)]
        section_description = " > ".join(heading_parts) if heading_parts else "Content"
        metadata_entry = {
            "source": f"{source.lower().replace(' ', '-')}-{len(grouped_docs[source]['metadata'])+1}",
            "name": f"{doc_title} - {section_description}"
        }
        grouped_docs[source]["metadata"].append(metadata_entry)

        # Add the distance/score
        grouped_docs[source]["distances"].append(doc.get("score", 0))

    # Convert the grouped documents into the desired format
    current_time = int(datetime.now().timestamp())
    for source_name, group_data in grouped_docs.items():
        if not group_data["documents"]:
            continue

        # Find the first document with this source to get reference_url if available
        reference_url = next((
            doc.get("metadata", {}).get("reference_url")
            for doc in unique_docs.values()
            if doc.get("metadata", {}).get("source") == source_name
        ), None)

        source_entry = {
            "source": {
                "name": source_name,
                "url": reference_url,
                "description": reference_url or f"Source: {source_name}",
                "created_at": current_time,
                "updated_at": current_time,
                "type": "collection",
            },
            "document": group_data["documents"],
            "metadata": group_data["metadata"],
            "distances": group_data["distances"]
        }

        result["data"]["sources"].append(source_entry)

    return result

class Pipe:
    class Valves(BaseModel):
        NAME_PREFIX: str = Field(
            default="aihub/",
            description="Prefix to be added before model names.",
        )
        AIHUB_API_BASE_URL: str = Field(
            default="http://localhost:8000/api/v1/openai",
            description="Base URL for accessing OpenAI API endpoints.",
        )
        AIHUB_API_KEY: str = Field(
            default="",
            description="API key for authenticating requests to the OpenAI API.",
        )
        EVENT_API_BASE_URL: str = Field(
            default="http://localhost:8000/api/v1/event",
            description="Base URL for accessing event API endpoints.",
        )

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self):
        """Get available models (synchronous method)"""
        if not self.valves.AIHUB_API_KEY:
            return [{"id": "error", "name": "API Key not provided."}]

        try:
            headers = {
                "Authorization": f"Bearer {self.valves.AIHUB_API_KEY}",
                "Content-Type": "application/json",
            }

            r = requests.get(f"{self.valves.AIHUB_API_BASE_URL}/models", headers=headers)
            r.raise_for_status()
            models = r.json()

            return [
                {
                    "id": model["id"],
                    "name": f'{self.valves.NAME_PREFIX}{model.get("name", model["id"])}',
                }
                for model in models.get("data", [])
            ]
        except Exception as e:
            logger.exception(f"Error fetching models: {e}")
            return [{"id": "error", "name": f"Error fetching models: {e}"}]

    async def get_retriever_events(self, thread_id: str, display_id: str, headers: dict) -> List[Dict]:
        """Query the event API for RetrieverEvents asynchronously"""
        params = {
            "thread_id": thread_id,
            "display_id": display_id,
            "event_class": "RetrieverEvent"
        }

        # Remove content-type header for GET request
        headers_copy = {k: v for k, v in headers.items() if k.lower() != "content-type"}

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(
                    self.valves.EVENT_API_BASE_URL,
                    params=params,
                    headers=headers_copy
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_body = await e.response.aread()
                logger.exception(f"HTTP error querying events: {e.response.status_code} - {error_body.decode()}")
                return []
            except Exception as e:
                logger.exception(f"Exception in getting retriever events: {e}")
                return []

    async def pipe_stream(
        self, body: dict, __user__: dict, __metadata__: dict, __event_emitter__, __request__
    ):
        """
        Handle streaming requests, yielding SSE formatted strings.
        This is an async generator function that yields lines of streaming output.
        """
        # Prepare headers and payload
        headers = {
            "Authorization": f"Bearer {self.valves.AIHUB_API_KEY}",
            "Content-Type": "application/json",
            "Accept-Language": __request__.headers.get("Accept-Language", "en-US,en;q=0.9"),
            **user_header(__user__),
        }

        model_id = body["model"].split(".", 1)[1] if "." in body["model"] else body["model"]
        thread_id = str_to_object_id(__metadata__.get("chat_id"))
        display_id = str_to_object_id(__metadata__.get("message_id"))

        payload = {
            **body,
            "model": model_id,
            "metadata": {
                "thread_id": thread_id,
                "display_id": display_id,
            },
        }

        # Create a streaming client with infinite timeout
        client = httpx.AsyncClient(timeout=None, follow_redirects=True)

        try:
            # Start the streaming request
            async with client.stream(
                    "POST",
                    url=f"{self.valves.AIHUB_API_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                ) as stream_response:

                # Process the stream line by line
                async for line in stream_response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue

                    # Format and yield as SSE string
                    if line.startswith("data:"):
                        yield f"{line}\n\n"
                    elif line == "[DONE]":
                        yield f"data: {line}\n\n"
                        break
                    else:
                        yield f"data: {line}\n\n"

                    # Check for finish_reason to detect stream end
                    if line.startswith("data: "):
                        try:
                            data_content = line[6:]
                            if data_content != "[DONE]":
                                data = json.loads(data_content)
                                if data.get('choices', [{}])[0].get('finish_reason'):
                                    # Stream near completion, but don't break yet
                                    pass
                        except Exception:
                            # Ignore JSON parsing errors
                            pass

                # Close the response when streaming is done
                await stream_response.aclose()

        except httpx.HTTPStatusError as e:
            try:
                error_body = await e.response.aread()
                error_detail = error_body.decode()
            except Exception:
                error_detail = "(Could not decode error body)"

            logger.exception(f"HTTP error during streaming: {e.response.status_code} - {error_detail}")
            yield f"data: {json.dumps({'error': f'API Error: Status {e.response.status_code}'})}\n\n"

        except Exception as e:
            logger.exception(f"Error during streaming: {e}")
            yield f"data: {json.dumps({'error': f'Request error: {str(e)}'})}\n\n"

        finally:
            # Always close the client when we're done
            await client.aclose()

            # After streaming is complete, query for retriever events
            try:
                logger.debug("Stream completed, querying for retriever events")
                retriever_events = await self.get_retriever_events(thread_id, display_id, headers)
                if retriever_events:
                    sources = transform_events_to_sources(retriever_events)
                    await __event_emitter__(sources)
                    logger.debug(f"Emitted sources with {len(sources['data']['sources'])} sources")
                else:
                    logger.debug("No retriever events found after stream completed")
            except Exception as e:
                logger.exception(f"Error processing retriever events: {e}")

    async def pipe_non_stream(
        self, body: dict, __user__: dict, __metadata__: dict, __event_emitter__, __request__
    ):
        """
        Handle non-streaming requests, returning a dict with the completion response.
        This is a regular async function that returns a dictionary.
        """
        # Prepare headers and payload
        headers = {
            "Authorization": f"Bearer {self.valves.AIHUB_API_KEY}",
            "Content-Type": "application/json",
            "Accept-Language": __request__.headers.get("Accept-Language", "en-US,en;q=0.9"),
            **user_header(__user__),
        }

        model_id = body["model"].split(".", 1)[1] if "." in body["model"] else body["model"]
        thread_id = str_to_object_id(__metadata__.get("chat_id"))
        display_id = str_to_object_id(__metadata__.get("message_id"))

        payload = {
            **body,
            "model": model_id,
            "metadata": {
                "thread_id": thread_id,
                "display_id": display_id,
            },
        }

        try:
            # Use a separate client for non-streaming requests
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.post(
                    url=f"{self.valves.AIHUB_API_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                completion_response = response.json()

            # Query for retriever events
            logger.debug("Non-streaming request completed, querying for retriever events")
            retriever_events = await self.get_retriever_events(thread_id, display_id, headers)
            if retriever_events:
                sources = transform_events_to_sources(retriever_events)
                await __event_emitter__(sources)
                logger.debug(f"Emitted sources with {len(sources['data']['sources'])} sources")

            # Return the complete response for non-streaming
            return completion_response

        except httpx.HTTPStatusError as e:
            try:
                error_body = await e.response.aread()
                error_detail = error_body.decode()
            except Exception:
                error_detail = "(Could not decode error body)"

            logger.exception(f"HTTP error: {e.response.status_code} - {error_detail}")
            return {"error": f"API Error: Status {e.response.status_code} - {error_detail}"}

        except Exception as e:
            logger.exception(f"Error during non-streaming request: {e}")
            return {"error": f"Request error: {str(e)}"}

    async def pipe(
        self, body: dict, __user__: dict, __metadata__: dict, __event_emitter__, __request__
    ):
        """
        Main entry point that dispatches to either streaming or non-streaming handler.

        This function acts as a dispatcher that determines whether to handle the request
        as a streaming request or a non-streaming request.
        """
        is_streaming = body.get("stream", False)
        logger.debug(f"Request type: {'streaming' if is_streaming else 'non-streaming'}")

        if is_streaming:
            # For streaming, we return the async generator object directly
            # Not awaiting it, as the caller will iterate over it
            return self.pipe_stream(body, __user__, __metadata__, __event_emitter__, __request__)
        else:
            # For non-streaming, we await the result and return it
            return await self.pipe_non_stream(body, __user__, __metadata__, __event_emitter__, __request__)