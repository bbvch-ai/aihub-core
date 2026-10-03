from typing import Annotated, Any

import httpx

from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_error import OpenTerminalError
from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_settings import OpenTerminalSettings


class OpenTerminalClient:
    """One user's view of the open-terminal sandbox, the same home that user's OpenWebUI chats work in.

    The sandbox keys homes by the `X-User-Id` it is sent and falls back to a shared account without one, so a client
    always carries the user's OpenWebUI id. Relative paths resolve against that home.
    """

    def __init__(
        self,
        openwebui_user_id: Annotated[str, "The user's OpenWebUI id, which picks their sandbox home."],
        settings: OpenTerminalSettings | None = None,
    ) -> None:
        self._settings = settings or OpenTerminalSettings()
        self._headers = {
            "Authorization": f"Bearer {self._settings.API_KEY.get_secret_value()}",
            "X-User-Id": openwebui_user_id,
        }

    async def execute(
        self, command: str, cwd: str | None = None, wait: float | None = None, tail: int | None = None
    ) -> dict[str, Any]:
        params = {"wait": wait, "tail": tail}
        return await self._json("POST", "/execute", params=params, json={"command": command, "cwd": cwd}, wait=wait)

    async def process_status(
        self, process_id: str, wait: float | None = None, offset: int | None = None, tail: int | None = None
    ) -> dict[str, Any]:
        params = {"wait": wait, "offset": offset, "tail": tail}
        return await self._json("GET", f"/execute/{process_id}/status", params=params, wait=wait)

    async def send_input(self, process_id: str, text: str) -> dict[str, Any]:
        return await self._json("POST", f"/execute/{process_id}/input", json={"input": text})

    async def kill(self, process_id: str, force: bool = False) -> dict[str, Any]:
        return await self._json("DELETE", f"/execute/{process_id}", params={"force": force})

    async def list_processes(self) -> list[dict[str, Any]]:
        return await self._json("GET", "/execute")

    async def list_files(self, directory: str) -> dict[str, Any]:
        return await self._json("GET", "/files/list", params={"directory": directory})

    async def read_file(self, path: str, start_line: int | None = None, end_line: int | None = None) -> dict[str, Any]:
        params = {"path": path, "start_line": start_line, "end_line": end_line}
        return await self._json("GET", "/files/read", params=params)

    async def write_file(self, path: str, content: str) -> dict[str, Any]:
        return await self._json("POST", "/files/write", json={"path": path, "content": content})

    async def replace_file_content(self, path: str, replacements: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._json("POST", "/files/replace", json={"path": path, "replacements": replacements})

    async def grep(
        self,
        query: str,
        path: str,
        regex: bool = False,
        case_insensitive: bool = False,
        include: list[str] | None = None,
        max_results: int | None = None,
    ) -> dict[str, Any]:
        params = {
            "query": query,
            "path": path,
            "regex": regex,
            "case_insensitive": case_insensitive,
            "include": include,
            "max_results": max_results,
        }
        return await self._json("GET", "/files/grep", params=params)

    async def glob(
        self, pattern: str, path: str, exclude: list[str] | None = None, max_results: int | None = None
    ) -> dict[str, Any]:
        params = {"pattern": pattern, "path": path, "exclude": exclude, "max_results": max_results}
        return await self._json("GET", "/files/glob", params=params)

    async def upload(self, directory: str, filename: str, content: bytes) -> dict[str, Any]:
        files = {"file": (filename, content)}
        return await self._json("POST", "/files/upload", params={"directory": directory}, files=files)

    async def mkdir(self, path: str) -> dict[str, Any]:
        return await self._json("POST", "/files/mkdir", json={"path": path})

    async def move(self, source: str, destination: str) -> dict[str, Any]:
        return await self._json("POST", "/files/move", json={"source": source, "destination": destination})

    async def delete(self, path: str) -> dict[str, Any]:
        """Removes a file, or a folder with everything in it."""
        return await self._json("DELETE", "/files/delete", params={"path": path})

    async def view(self, path: str) -> tuple[bytes, str]:
        """A file's raw bytes and type; unlike reading, this works for any file, binary documents included.

        Streamed and stopped at the size limit, so a huge file the code made is refused instead of filling memory."""
        async with self._http() as http, http.stream("GET", "/files/view", params={"path": path}) as response:
            if response.is_error:
                await response.aread()
                raise self._error(response)
            content = bytearray()
            async for chunk in response.aiter_bytes():
                content.extend(chunk)
                if len(content) > self._settings.MAX_FILE_BYTES:
                    raise OpenTerminalError(
                        f"{path} is larger than {self._settings.MAX_FILE_BYTES} bytes, the most a file may have here."
                    )
            return bytes(content), response.headers.get("content-type", "application/octet-stream")

    async def _json(self, method: str, path: str, wait: float | None = None, **kwargs: Any) -> Any:
        return (await self._request(method, path, wait=wait, **kwargs)).json()

    async def _request(self, method: str, path: str, wait: float | None = None, **kwargs: Any) -> httpx.Response:
        if "params" in kwargs:
            kwargs["params"] = {key: value for key, value in kwargs["params"].items() if value is not None}
        async with self._http(wait) as http:
            response = await http.request(method, path, **kwargs)
        if response.is_error:
            raise self._error(response)
        return response

    def _http(self, wait: float | None = None) -> httpx.AsyncClient:
        timeout = self._settings.TIMEOUT + (wait or 0)
        return httpx.AsyncClient(base_url=self._settings.BASE_URL, headers=self._headers, timeout=timeout)

    @classmethod
    def _error(cls, response: httpx.Response) -> OpenTerminalError:
        return OpenTerminalError(f"{response.status_code}: {cls._reason(response)}", response.status_code)

    @staticmethod
    def _reason(response: httpx.Response) -> str:
        try:
            return str(response.json().get("detail", response.text))
        except ValueError:
            return response.text
