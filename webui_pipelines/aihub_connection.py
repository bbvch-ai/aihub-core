from pydantic import BaseModel, Field
import requests
import hashlib
from typing import Optional
from bson import ObjectId


def str_to_object_id(context_id: Optional[str]) -> ObjectId:
    if not context_id:
        return ObjectId()
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
            print(models)
            return [
                {
                    "id": model["id"],
                    "name": f'{self.valves.NAME_PREFIX}{model.get("name", model["id"])}',
                }
                for model in models["data"]
            ]

        except Exception as e:
            print("Exception in getting models", e)
            return [
                {
                    "id": "error",
                    "name": "Error fetching models.",
                },
            ]

    def pipe(self, body: dict, __user__: dict, __metadata__: dict):
        print("user", __user__)
        headers = {
            "Authorization": f"Bearer {self.valves.AIHUB_API_KEY}",
            "Content-Type": "application/json",
            **user_header(__user__),
        }

        # Extract model id from the model name
        model_id = body["model"][body["model"].find(".") + 1 :]

        # Update the model id in the body
        payload = {
            **body,
            "model": model_id,
            "metadata": {
                "thread_id": str_to_object_id(__metadata__.get("chat_id")),
                "display_id": str_to_object_id(__metadata__.get("message_id")),
            },
        }
        try:
            r = requests.post(
                url=f"{self.valves.AIHUB_API_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                stream=True,
            )

            r.raise_for_status()

            if body.get("stream", False):
                return r.iter_lines()
            else:
                return r.json()
        except Exception as e:
            return f"Error: {e}"
