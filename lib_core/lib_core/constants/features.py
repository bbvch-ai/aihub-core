from enum import Enum


class FeatureFlag(Enum):
    PROMPT_ENHANCE = "prompt_enhance"
    PROMPT_LIBRARY = "prompt_library"
    VOICE_INPUT = "voice_input"
    VOICE_OUTPUT = "voice_output"
    TRACING = "tracing"
    TRACE_USER = "trace_user"
    USAGE_LIMITS = "usage_limits"
    CHAT_EXPORT_IMPORT = "chat_export_import"
    SAVE_QUESTIONS = "save_questions"
    SAVE_CHAT_HISTORY = "save_chat_history"
