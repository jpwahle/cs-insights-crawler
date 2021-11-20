import logging
import os
import sys
from typing import TypeVar

__ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
__TOP_LEVEL_PATH = os.path.join(__ROOT_DIR, "../..")


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] - %(module)s -  %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler("{0}/{1}.log".format(__TOP_LEVEL_PATH, "trading_engine")),
    ],
)

T = TypeVar("T", bound="LogMixin")


class LogMixin(object):
    @property
    def logger(self: T) -> logging.Logger:
        name = ".".join([__name__, self.__class__.__name__])
        return logging.getLogger(name)

    @property
    def long_opertaion_log(self: T) -> str:
        return "This may take a while..."

    def log_stacktrace(self: T, message: str, error: Exception) -> None:
        self.logger.error(message)
        self.logger.exception(error)
