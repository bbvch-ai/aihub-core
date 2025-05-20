import logging

import colorlog

from aihub_lib.testing.logging.LoggingConfig import LoggingConfig


def enable_logging(level: str | int = logging.DEBUG, lib_level: str | int = logging.WARNING) -> logging.Logger:
    """
    The log level will ALWAYS be set to the LOG_LEVEL specified in the environment variables, if set.
    """

    config = LoggingConfig()
    if config.LOG_LEVEL is not None:
        level = config.LOG_LEVEL
        lib_level = config.LOG_LEVEL

    lib_loggers = [
        "azure.identity",
        "azure.core.pipeline",
        "azure.core.pipeline.policies",
        "azure.core.pipeline.transport",
        "urllib3",
        "pymongo",
        "httpx",
        "httpcore",
    ]

    for logger_name in lib_loggers:
        logging.getLogger(logger_name).setLevel(lib_level)

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
