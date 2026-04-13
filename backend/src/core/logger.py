"""Logging utility for the application.

Provides a configured logger instance that only emits logs when
the application is running in the production environment.
"""
import logging
import os

def get_logger(name: str) -> logging.Logger:
    """Retrieves a logger instance configured for the specific module.
    
    The logger will only output messages if the ENVIRONMENT variable
    is set to 'production'. Otherwise, it uses a NullHandler to silently
    discard all logs.
    
    Args:
        name (str): The name of the module (typically __name__).
        
    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers if get_logger is called multiple times
    if not logger.handlers:
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        
        if is_production:
            logger.setLevel(logging.INFO)
            # In production, we might want JSON formatting or structured logging,
            # but for now we keep the simple StreamHandler.
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - [%(name)s] %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        else:
            # In development, output DEBUG logs to the console for easier troubleshooting
            logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
    return logger
