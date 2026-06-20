import sys
from loguru import logger
from app.core.config import settings


def setup_logging() -> None:
    """Configure Loguru for the application."""
    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    if settings.app_env != "development":
        logger.add(
            "logs/estia.log",
            level="INFO",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
        )

    logger.info(
        f"Logging configured — level={settings.log_level}, env={settings.app_env}"
    )
