"""This module implements basic logging functionality for all classes as a MixIn."""
import logging
import os
import sys
from typing import Any, Dict, TypeVar

__ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
__TOP_LEVEL_PATH = os.path.join(__ROOT_DIR, "../..")


def set_glob_logger(verbose: bool, **kwargs: Dict[str, Any]) -> None:
    """Set the predefined logger args for the whole project.

    Args:
        verbose (bool): Whether to print a lot (i.e., whether to show debug messages) or not.
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.ERROR,
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
        return "this may take a while..."

    def log_stacktrace(self: T, message: str, error: Exception) -> None:
        self.logger.error(message)
        self.logger.exception(error)
