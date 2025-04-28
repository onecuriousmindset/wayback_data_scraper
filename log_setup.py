"""Colourful logger shared by all modules."""
import logging
import sys
from pathlib import Path
from colorama import init as colorama_init, Fore, Style

colorama_init(autoreset=True)

# Create log directory if it doesn't exist
log_dir = Path("log")
log_dir.mkdir(exist_ok=True)

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

class _Logger(logging.Logger):
    def success(self, msg, *args, **kwargs):
        if self.isEnabledFor(SUCCESS_LEVEL):
            self._log(SUCCESS_LEVEL, msg, args, **kwargs)

logging.setLoggerClass(_Logger)
logger = logging.getLogger("spaargids")
logger.setLevel(logging.DEBUG)

class ColourFormatter(logging.Formatter):
    COLOURS = {
        logging.DEBUG: Fore.WHITE,
        logging.INFO: Fore.CYAN,
        SUCCESS_LEVEL: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        colour = self.COLOURS.get(record.levelno, "")
        reset = Style.RESET_ALL if colour else ""
        record.msg = f"{colour}{record.msg}{reset}"
        return super().format(record)

_console_fmt = "%(asctime)s %(levelname)-8s %(message)s"
_file_fmt = "%(asctime)s [%(levelname)s] %(message)s"

# console handler (DEBUG+)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)  # Changed from INFO to DEBUG
ch.setFormatter(ColourFormatter(_console_fmt, "%H:%M:%S"))

# file handler (DEBUG)
fh = logging.FileHandler(log_dir / "spaargids_extractor.log", encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter(_file_fmt, "%Y-%m-%d %H:%M:%S"))

logger.addHandler(ch)
logger.addHandler(fh)

# Helpful aliases for quick import
info = logger.info
success = logger.success
warning = logger.warning
error = logger.error
debug = logger.debug
