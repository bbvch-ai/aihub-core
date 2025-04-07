from pydantic import BaseModel, Field
import requests
import hashlib
import uuid
import json
from typing import Optional, List, Dict, Any, Generator, AsyncGenerator
from bson import ObjectId
import asyncio

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
    from datetime import datetime

    result = {
        "type": "chat:completion",
        "data": {
            "sources": []
        }
    }

    # Deduplicate documents by their id
    unique_docs = {}

    # Process each retriever event and extract documents
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
            grouped_docs[source] = {
                "documents": [],
                "metadata": [],
                "distances": []
            }

        # Add document content
        content = doc.get("content", "")
        grouped_docs[source]["documents"].append(content)

        # Create metadata entry
        doc_title = metadata.get("document_title", "Document")
        heading_parts = []

        # Add any available headings
        for h in ["h1", "h2", "h3"]:
            if metadata.get(h):
                heading_parts.append(metadata.get(h))

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
        if not self.valves.AIHUB_API_KEY:
            return [
                {
                    "id": "error",
                    "name": "API Key not provided.",
                },
            ]

        try:
            headers = {
                "Authorization": f"Bearer {self.valves.AIHUB_API_KEY}",
                "Content-Type": "application/json",
            }

            r = requests.get(
                f"{self.valves.AIHUB_API_BASE_URL}/models", headers=headers
            )
            models = r.json()
            return [
                {
                    "id": model["id"],
                    "name": f'{self.valves.NAME_PREFIX}{model.get("name", model["id"])}',
                }
                for model in models["data"]
            ]

        except Exception as e:
            return [
                {
                    "id": "error",
                    "name": "Error fetching models.",
                },
            ]

    async def get_retriever_events(self, thread_id: str, display_id: str, headers: dict):
        """Query the event API for RetrieverEvents"""
        params = {
            "thread_id": thread_id,
            "display_id": display_id,
            "event_class": "RetrieverEvent"
        }

        try:
            # Remove content-type header for GET request
            headers_copy = {k: v for k, v in headers.items() if k != "Content-Type"}

            response = requests.get(
                self.valves.EVENT_API_BASE_URL,
                params=params,
                headers=headers_copy
            )

            if response.status_code != 200:
                logger.error(f"Error querying events: {response.status_code} - {response.text}")
                return []

            return response.json()
        except Exception as e:
            logger.debug(f"Exception in getting retriever events: {e}")
            return []

    async def handle_stream_and_query_sources(self, stream_iter, thread_id, display_id, headers, event_emitter):
        """
        Handle streaming response and query sources after stream completes.

        This generator proxies the stream and detects when it's finished,
        then queries for sources and emits them via the event_emitter.
        """
        try:
            # Proxy through all lines from the stream
            for line in stream_iter:
                yield line

                # Check if this line represents the end of the stream
                try:
                    # For OpenAI-compatible streams, the end is typically signaled by "[DONE]" or
                    # a data field with finish_reason
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line == "[DONE]":
                            break
                        if decoded_line.startswith('data: '):
                            data = json.loads(decoded_line[6:])
                            if data.get('choices', [{}])[0].get('finish_reason'):
                                # One more line might follow, but we're near the end
                                pass
                except Exception:
                    # Ignore errors in parsing, just continue streaming
                    pass

            # If we get here, the stream has ended (or we broke out of the loop)
            # Now query for RetrieverEvents
            logger.debug("Stream completed, querying for retriever events")
            retriever_events = await self.get_retriever_events(thread_id, display_id, headers)

            if retriever_events:
                sources = transform_events_to_sources(retriever_events)
                await event_emitter(sources)
                logger.debug(f"Emitted sources with {len(sources['data']['sources'])} sources")
            else:
                logger.debug("No retriever events found after stream completed")

        except Exception as e:
            logger.error(f"Error in stream handling: {e}")
            # Still yield any remaining lines to avoid breaking the client
            for line in stream_iter:
                yield line

    async def pipe(
            self, body: dict, __user__: dict, __metadata__: dict, __event_emitter__
    ):
        headers = {
            "Authorization": f"Bearer {self.valves.AIHUB_API_KEY}",
            "Content-Type": "application/json",
            **user_header(__user__),
        }

        # Extract model id from the model name
        model_id = body["model"].split(".", 1)[1] if "." in body["model"] else body["model"]

        # Get thread_id and display_id
        thread_id = str_to_object_id(__metadata__.get("chat_id"))
        display_id = str_to_object_id(__metadata__.get("message_id"))

        # Prepare payload
        payload = {
            **body,
            "model": model_id,
            "metadata": {
                "thread_id": thread_id,
                "display_id": display_id,
            },
        }

        try:
            # Make the API request for chat completion
            r = requests.post(
                url=f"{self.valves.AIHUB_API_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                stream=body.get("stream", False)
            )

            r.raise_for_status()

            # Handle streaming responses
            if body.get("stream", False):
                # Get the raw stream iterator
                stream_iter = r.iter_lines()

                # Return our own generator that will handle the stream and query sources after completion
                return self.handle_stream_and_query_sources(
                    stream_iter=stream_iter,
                    thread_id=thread_id,
                    display_id=display_id,
                    headers=headers,
                    event_emitter=__event_emitter__
                )
            else:
                # For non-streaming responses
                completion_response = r.json()

                # Query for RetrieverEvents
                retriever_events = await self.get_retriever_events(thread_id, display_id, headers)

                if retriever_events:
                    sources = transform_events_to_sources(retriever_events)
                    await __event_emitter__(sources)

                return completion_response
        except Exception as e:
            return f"Error: {e}"