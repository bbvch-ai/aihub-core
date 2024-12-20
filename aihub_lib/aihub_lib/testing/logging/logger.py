import logging
import colorlog


def enable_logging(level=logging.DEBUG):
    azure_loggers = [
        'azure.identity',
        'azure.core.pipeline',
        'azure.core.pipeline.policies',
        'azure.core.pipeline.transport',
        'urllib3',
        'pymongo',
        'httpx'
    ]

    for logger_name in azure_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    handler = logging.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(name)s.%(funcName)s] %(levelname)s: %(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
    )

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger