"""Model infos as `/v1/model/info` reports them, one per way a model can pass or fail a picker's requirements."""

from swiss_ai_hub.api.routes.model.dto.model_dto import ModelDTO

_ALL_FLAGS = {
    "supports_function_calling": True,
    "supports_response_schema": True,
    "supports_vision": True,
    "supports_reasoning": True,
}

FAKE_MODELS = [
    ModelDTO.model_validate(model)
    for model in [
        {
            "model_name": "text-generation/fake-swiss",
            "model_info": {"mode": "chat", "aihub_hosting_location": "swiss_cloud", "aihub_general_purpose": True}
            | _ALL_FLAGS,
        },
        {
            "model_name": "text-generation/fake-eu",
            "model_info": {"mode": "chat", "aihub_hosting_location": "eu", "aihub_general_purpose": True} | _ALL_FLAGS,
        },
        {
            "model_name": "text-generation/fake-no-tools",
            "model_info": {"mode": "chat", "aihub_hosting_location": "swiss_cloud", "aihub_general_purpose": True}
            | _ALL_FLAGS
            | {"supports_function_calling": False},
        },
        {
            "model_name": "text-generation/fake-ocr",
            "model_info": {
                "mode": "chat",
                "aihub_hosting_location": "swiss_cloud",
                "aihub_general_purpose": False,
                "supports_function_calling": False,
                "supports_response_schema": False,
                "supports_vision": True,
                "supports_reasoning": False,
            },
        },
        {"model_name": "text-generation/fake-undeclared", "model_info": {"mode": "chat"}},
        {"model_name": "embedding/fake-embedding", "model_info": {"mode": "embedding"}},
    ]
]
