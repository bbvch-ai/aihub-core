import base64

import pytest
from fastapi import HTTPException

from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest

PDF = base64.b64encode(b"%PDF-1.4 test").decode()


def request_with(*messages: dict) -> ChatCompletionRequest:
    return ChatCompletionRequest.model_validate({"model": "Agent/id", "messages": list(messages)})


def file_part(file: dict) -> dict:
    return {"type": "file", "file": file}


def test_reads_the_file_parts_of_the_last_user_message():
    request = request_with(
        {
            "role": "user",
            "content": [file_part({"filename": "old.pdf", "file_data": f"data:application/pdf;base64,{PDF}"})],
        },
        {"role": "assistant", "content": "Read it."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "And this one?"},
                file_part({"filename": "new.pdf", "file_data": f"data:application/pdf;base64,{PDF}"}),
            ],
        },
    )

    files = request.inline_files()

    assert [(file.filename, file.file_type, file.content) for file in files] == [("new.pdf", "application/pdf", PDF)]


def test_the_message_text_survives_the_extraction():
    request = request_with(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Summarise"},
                file_part({"filename": "a.pdf", "file_data": f"data:application/pdf;base64,{PDF}"}),
            ],
        }
    )

    request.inline_files()

    assert request.llama_index_messages[-1].content == "Summarise"


def test_plain_base64_takes_its_type_from_the_filename():
    request = request_with({"role": "user", "content": [file_part({"filename": "a.pdf", "file_data": PDF})]})
    assert request.inline_files()[0].file_type == "application/pdf"


def test_a_hosted_file_reference_is_refused():
    request = request_with({"role": "user", "content": [file_part({"file_id": "file-abc"})]})
    with pytest.raises(HTTPException) as rejected:
        request.inline_files()
    assert rejected.value.status_code == 400


def test_a_text_only_request_has_no_files():
    assert request_with({"role": "user", "content": "Hi"}).inline_files() == []
