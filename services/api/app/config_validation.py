"""
Runtime configuration validation for Feltabout.

These checks keep local development easy while preventing common production
misconfiguration mistakes such as launching with dev secrets or placeholder
credentials.
"""

import logging
import os

logger = logging.getLogger(__name__)

_DEV_JWT_SECRETS = {
    "dev-secret-change-in-production",
    "dev-secret",
    "change-me",
    "changeme",
}

_PLACEHOLDER_PASSWORDS = {
    "change-me-in-prod",
    "postgres",
    "password",
    "changeme",
}


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def validate_runtime_config() -> None:
    """
    Validate environment configuration at API startup.

    Local development remains permissive. Production-like mode is triggered by
    APP_ENV=production/staging or USE_AUTH=true.
    """
    app_env = os.environ.get("APP_ENV", os.environ.get("ENV", "development")).strip().lower()
    use_auth = _truthy(os.environ.get("USE_AUTH", "false"))
    production_like = app_env in {"prod", "production", "staging"} or use_auth

    jwt_secret = os.environ.get("JWT_SECRET", "")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "")
    database_url = os.environ.get("DATABASE_URL", "")
    allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
    allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]
    email_enabled = _truthy(os.environ.get("EMAIL_ENABLED", "false"))

    errors: list[str] = []
    warnings: list[str] = []

    if use_auth and (
        not jwt_secret
        or jwt_secret in _DEV_JWT_SECRETS
        or len(jwt_secret) < 32
    ):
        errors.append(
            "USE_AUTH=true requires a strong JWT_SECRET of at least 32 characters."
        )

    if production_like:
        if postgres_password in _PLACEHOLDER_PASSWORDS or "change-me-in-prod" in database_url:
            errors.append(
                "Production-like mode cannot use the placeholder database password."
            )

        if not allowed_origins:
            errors.append("Production-like mode requires explicit ALLOWED_ORIGINS.")
        elif "*" in allowed_origins:
            errors.append("Production-like mode cannot use wildcard ALLOWED_ORIGINS.")
        elif all(origin.startswith("http://localhost") for origin in allowed_origins):
            warnings.append(
                "ALLOWED_ORIGINS only contains localhost origins. Add deployed frontend origins before launch."
            )

    if email_enabled:
        warnings.append(
            "EMAIL_ENABLED=true is set, but provider delivery is not implemented in MVP 1. Magic links still log to the server console."
        )

    for warning in warnings:
        logger.warning("Config warning: %s", warning)

    if errors:
        raise RuntimeError("Invalid Feltabout configuration: " + " ".join(errors))
