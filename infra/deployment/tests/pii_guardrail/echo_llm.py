"""OpenAI-compatible stub for the guardrail's end-to-end tests: it answers with what it received.

The reply is the last user message as the provider saw it (masked), streamed in small pieces when asked, or, when the
request offers tools, a call to the first tool whose arguments carry that message. Every request's messages are
appended to RECEIVED_LOG, which shows exactly what a real model would have seen.
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CHUNK_CHARS = int(os.environ.get("CHUNK_CHARS", "8"))
CHUNK_DELAY_SECONDS = float(os.environ.get("CHUNK_DELAY_MS", "20")) / 1000
RECEIVED_LOG = os.environ.get("RECEIVED_LOG", "/out/received.jsonl")


class EchoHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt = next(m["content"] for m in reversed(body["messages"]) if m["role"] == "user")
        if isinstance(prompt, list):
            prompt = " ".join(p.get("text", "") for p in prompt if isinstance(p, dict))
        with open(RECEIVED_LOG, "a", encoding="utf-8") as log:
            log.write(json.dumps({"messages": body["messages"]}, ensure_ascii=False) + "\n")
        tool = (body.get("tools") or [{}])[0].get("function", {}).get("name")
        arguments = json.dumps({"query": prompt}, ensure_ascii=False) if tool else None
        if body.get("stream"):
            self.stream(body["model"], prompt, tool, arguments)
        else:
            self.reply(body["model"], prompt, tool, arguments)

    def reply(self, model: str, prompt: str, tool: str | None, arguments: str | None) -> None:
        message = {"role": "assistant", "content": None if tool else prompt}
        if tool:
            message["tool_calls"] = [{"id": "call-1", "type": "function",
                                      "function": {"name": tool, "arguments": arguments}}]
        payload = json.dumps({
            "id": "echo-1", "object": "chat.completion", "created": int(time.time()), "model": model,
            "choices": [{"index": 0, "finish_reason": "tool_calls" if tool else "stop", "message": message}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def stream(self, model: str, prompt: str, tool: str | None, arguments: str | None) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        text = arguments if tool else prompt
        pieces = [text[i:i + CHUNK_CHARS] for i in range(0, len(text), CHUNK_CHARS)]
        for index, piece in enumerate(pieces):
            if tool:
                call = {"index": 0, "function": {"arguments": piece}}
                if index == 0:
                    call.update(id="call-1", type="function", function={"name": tool, "arguments": piece})
                delta = {"tool_calls": [call]}
            else:
                delta = {"content": piece}
            if index == 0:
                delta["role"] = "assistant"
            self.event(model, delta, None)
            time.sleep(CHUNK_DELAY_SECONDS)
        self.event(model, {}, "tool_calls" if tool else "stop")
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def event(self, model: str, delta: dict, finish_reason: str | None) -> None:
        payload = {"id": "echo-1", "object": "chat.completion.chunk", "created": int(time.time()), "model": model,
                   "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}]}
        self.wfile.write(b"data: " + json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n\n")
        self.wfile.flush()

    def log_message(self, format: str, *args) -> None:
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), EchoHandler).serve_forever()
