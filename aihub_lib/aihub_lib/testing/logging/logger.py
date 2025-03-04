import logging
import os

import colorlog


def enable_logging(level=logging.DEBUG):
    if os.environ.get("DISABLE_LOGGING"):
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)
        return logger

    azure_loggers = [
        "azure.identity",
        "azure.core.pipeline",
        "azure.core.pipeline.policies",
        "azure.core.pipeline.transport",
        "urllib3",
        "pymongo",
        "httpx",
    ]

    for logger_name in azure_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

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

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger
