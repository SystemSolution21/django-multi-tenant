# utils/app_logger.py

# Import standard libraries
from pathlib import Path
from typing import Any


def get_logging_config(
    base_dir: str | Path,
    app_names: list[str] | None = None,
    console_log_level: str = "INFO",
) -> dict[str, Any]:
    """
    Generates a logging configuration dictionary.

    :param base_dir: The base directory of the Django project.
    :param app_names: List of application names to configure loggers for.
    :param console_log_level: The logging level for the console handler (e.g., "DEBUG", "INFO").
    :return: A dictionary with the logging configuration.
    """
    if app_names is None:
        app_names = []

    # Project base directory
    base_dir = Path(base_dir)

    # Ensure logs directory exists
    logs_dir: Path = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Define loggers for specific apps
    custom_loggers: dict[str, dict[str, Any]] = {}
    for app in app_names:
        custom_loggers[app] = {
            "handlers": ["console", "rotating_app_log", "rotating_error_log"],
            "level": "INFO",
            "propagate": False,
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} {module} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": console_log_level.upper(),
                "formatter": "verbose",
            },
            "rotating_app_log": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(logs_dir / "app.log"),
                "formatter": "verbose",
                "maxBytes": 1024 * 1024 * 5,  # 5 MB
                "backupCount": 5,
            },
            "rotating_error_log": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(logs_dir / "error.log"),
                "formatter": "verbose",
                "maxBytes": 1024 * 1024 * 5,  # 5 MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console", "rotating_app_log", "rotating_error_log"],
                "level": "INFO",
                "propagate": True,
            },
            **custom_loggers,
        },
    }
