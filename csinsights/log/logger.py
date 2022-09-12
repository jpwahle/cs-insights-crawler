"""This module implements basic logging functionality for all classes as a MixIn."""
import logging
import os
import sys
from typing import TypeVar

__ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
__TOP_LEVEL_PATH = os.path.join(__ROOT_DIR, "../..")


def set_glob_logger(verbose: bool, **kwargs: bool) -> None:
    """Set the predefined logger args for the whole project.

    Args:
        verbose (bool): Whether to print a lot (i.e., whether to show debug messages) or not.
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.ERROR,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] - %(module)s -  %(message)s",
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
            logging.FileHandler("{0}/{1}.log".format(__TOP_LEVEL_PATH, "csinsights")),
        ],
    )


T = TypeVar("T", bound="LogMixin")


class LogMixin(object):
    """Logger that can be mixed in all classes

    Args:
        object (_type_): Just the default python object
    """

    @property
    def logger(self: T) -> logging.Logger:
        """Returns the logger

        Args:
            self (T): The LogMixin Class

        Returns:
            logging.Logger: The logger that can print stuff to the console
        """
        name = ".".join([__name__, self.__class__.__name__])
        return logging.getLogger(name)

    @property
    def long_opertaion_log(self: T) -> str:
        """A default for long operation logs

        Args:
            self (T): The LogMixin Class

        Returns:
            str: The string indicating a long operation
        """
        return "this may take a while..."

    def log_stacktrace(self: T, message: str, error: Exception) -> None:
        """A function to log the stacktrace on errors

        Args:
            self (T): The LogMixin Class
            message (str): The message to print
            error (Exception): The exception that was thrown
        """
        self.logger.error(message)
        self.logger.exception(error)
