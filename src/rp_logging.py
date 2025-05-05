import atexit
import logging.config
import os
from logging import Handler
from logging.handlers import RotatingFileHandler


class SeparateFilenameRotatingFileHandler(Handler):
    def __init__(self, log_dir="logs", maxBytes=50000, backupCount=3, formatter=None):
        super().__init__()
        self.log_dir = log_dir
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self.formatter = formatter
        self.handlers = {}
        os.makedirs(self.log_dir, exist_ok=True)

    def emit(self, record):
        logger_name = record.name

        if logger_name not in self.handlers:
            filename = os.path.join(self.log_dir, f"{logger_name}.log")
            handler = RotatingFileHandler(
                filename, maxBytes=self.maxBytes, backupCount=self.backupCount
            )
            if self.formatter:
                handler.setFormatter(self.formatter)
            self.handlers[logger_name] = handler

        self.handlers[logger_name].emit(record)

    def close(self):
        for handler in self.handlers.values():
            handler.close()
        super().close()


DEFAULT_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "class": SeparateFilenameRotatingFileHandler,
            "level": "DEBUG",
            "formatter": "simple",
            # "filename": "my_app.log",
            "maxBytes": 10_000_000,
            "backupCount": 3,
        },
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            "handlers": ["stderr", "file"],
            "respect_handler_level": True,
        },
    },
    "loggers": {"root": {"level": "DEBUG", "handlers": ["queue_handler"]}},
}


def setup_logging():
    logging.config.dictConfig(DEFAULT_CONFIG)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
