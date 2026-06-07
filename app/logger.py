import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger("laundry")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))

        file_handler = logging.FileHandler(
            log_dir / f"laundry_{datetime.now().strftime('%Y%m%d')}.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()
