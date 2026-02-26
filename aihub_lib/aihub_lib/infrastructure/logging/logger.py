import logging

import colorlog

from aihub_lib.infrastructure.logging.LogSettings import LogSettings

_logging_configured = False


def enable_logging(level: int | None = None) -> logging.Logger:
    """
    Configure logging with colored output.

    The log level will be set from the LOG_LEVEL environment variable if not explicitly provided.
    Idempotent — calling multiple times only adds the handler once.
    """
    global _logging_configured  # noqa: PLW0603

    level = level if level is not None else LogSettings().level_number

    lib_loggers = [
        "azure.identity",
        "azure.core.pipeline",
        "azure.core.pipeline.policies",
        "azure.core.pipeline.transport",
        "urllib3",
        "pymongo",
        "httpx",
        "neo4j",
        "openai",
        "botocore",
        "mem0",
        "opentelemetry",
        "asyncio",
        "httpcore",
        "opentelemetry",
    ]

    for logger_name in lib_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if _logging_configured:
        return root_logger

    handler = logging.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s.%(msecs)03d] [%(name)s.%(funcName)s] %(levelname)s: %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger.addHandler(handler)
    _logging_configured = True

    return root_logger
