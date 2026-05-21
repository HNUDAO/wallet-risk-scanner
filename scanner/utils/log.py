import logging
import sys

_logger = logging.getLogger("wallet-risk-scanner")
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("[dim]%(message)s[/dim]"))
_logger.addHandler(_handler)
_logger.setLevel(logging.WARNING)

_verbose = False


def enable_verbose():
    global _verbose
    _verbose = True
    _logger.setLevel(logging.DEBUG)


def is_verbose():
    return _verbose


def debug(msg: str):
    _logger.debug(msg)


def info(msg: str):
    _logger.info(msg)


def warning(msg: str):
    _logger.warning(msg)
