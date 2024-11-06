# backend/utils.py

import logging

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
