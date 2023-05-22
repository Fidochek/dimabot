#!/bin/python3

from config import LOG_LEVEL

log_config = {
    "version": 1,
    "formatters": {
        "bot_formatter": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "bot_handler": {
            "class": "logging.FileHandler",
            "formatter": "bot_formatter",
            "filename": "bot.log",
            "encoding": "UTF-8",
        },
    },
    "loggers": {
        "bot": {
            "handlers": ["bot_handler"],
            "level": LOG_LEVEL,
            "filemod": "w",
        },
    },
}