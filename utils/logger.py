# utils/app_logger.py

# Import standard libraries
import logging
import threading
from pathlib import Path
from typing import Any

_thread_locals = threading.local()


class RequestMiddleware:
    """
    Middleware to store the current request in thread-local storage.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            # Clean up to prevent memory leaks/pollution
            if hasattr(_thread_locals, "request"):
                del _thread_locals.request
        return response


class RequestFilter(logging.Filter):
    """
    Filter to inject request information (user ID, path) into log records.
    """

    def filter(self, record):
        request = getattr(_thread_locals, "request", None)
        record.user_id = (
            request.user.email
            if request and hasattr(request, "user") and request.user.is_authenticated
            else "system"
        )
        record.path = getattr(request, "path", "N/A") if request else "N/A"
        return True


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
        "filters": {
            "request_context": {
                "()": "utils.logger.RequestFilter",
            },
        },
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} {module} [user:{user_id}] [path:{path}] {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "filters": ["request_context"],
                "class": "logging.StreamHandler",
                "level": console_log_level.upper(),
                "formatter": "verbose",
            },
            "rotating_app_log": {
                "filters": ["request_context"],
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(logs_dir / "app.log"),
                "formatter": "verbose",
                "maxBytes": 1024 * 1024 * 5,  # 5 MB
                "backupCount": 5,
            },
            "rotating_error_log": {
                "filters": ["request_context"],
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
