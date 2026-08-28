"""
ClipForge AI — Structured Logger
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from backend import config

# Ensure log dir exists
config.ensure_directories()

LOG_FILE = config.LOGS_DIR / "clipforge.log"

_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that writes to stdout and a rotating file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(_formatter)
    logger.addHandler(ch)

    # File handler (5 MB × 3 backups)
    try:
        fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(_formatter)
        logger.addHandler(fh)
    except Exception:
        pass  # Non-fatal if log file can't be created

    logger.propagate = False
    return logger


def job_logger(job_id: str, name: str = "worker") -> logging.Logger:
    """Return a logger prefixed with [JOB job_id]."""
    class JobFilter(logging.Filter):
        def filter(self, record):
            record.msg = f"[JOB {job_id}] {record.msg}"
            return True

    lg = get_logger(f"{name}.{job_id}")
    if not any(isinstance(f, JobFilter) for f in lg.filters):
        lg.addFilter(JobFilter())
    return lg
