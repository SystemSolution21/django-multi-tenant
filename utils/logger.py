# utils/logger.py

# Import standard libraries
import logging
from pathlib import Path
from typing import Any

# Import third-party libraries
import structlog


def configure_structlog():
    """
    Configure structlog processors and factory.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class RequireUserFilter(logging.Filter):
    """
    Filter to only allow log records that have a user_id attribute,
    which is added by structlog processors.
    """

    def filter(self, record) -> bool:
        # structlog processors add context and explicit log k-v pairs as
        # attributes on the LogRecord. We just need to check for existence.
        # structlog passes the event dictionary as record.msg when using wrap_for_formatter.
        # We need to check if user_id is present in that dictionary.
        if isinstance(record.msg, dict):
            return "user_id" in record.msg
        return hasattr(record, "user_id")


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

    # Ensure structlog is configured
    configure_structlog()

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
        "filters": {
            "require_user": {
                "()": "utils.logger.RequireUserFilter",
            },
        },
        "formatters": {
            "json_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
            "console_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": console_log_level.upper(),
                "formatter": "console_formatter",
            },
            "rotating_app_log": {
                # Only log to file if user is present (as per requirement)
                "filters": ["require_user"],
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(logs_dir / "app.log"),
                "formatter": "json_formatter",
                "maxBytes": 1024 * 1024 * 5,  # 5 MB
                "backupCount": 5,
            },
            "rotating_error_log": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(logs_dir / "error.log"),
                "formatter": "json_formatter",
                "maxBytes": 1024 * 1024 * 5,  # 5 MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "django": {
                # Django's internal logs should go to console and error file, but not the user-action app.log
                "handlers": ["console", "rotating_error_log"],
                "level": "INFO",  # Use "WARNING" in production to reduce noise
                "propagate": False,
            },
            "django_structlog": {
                "handlers": ["console", "rotating_error_log"],
                "level": "WARNING",  # Quiets the INFO-level request_started/finished logs
                "propagate": False,
            },
            **custom_loggers,
        },
    }
