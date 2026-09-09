"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
import os
from uuid import UUID

from dotenv import load_dotenv

load_dotenv()

DEFAULT_TENANT_ID = "c990bb7a-51f4-439b-bd36-9c07fb1041c0"
DEFAULT_API_CLIENT_ID = "e78c1e61-6047-47ed-8e6a-3a5ddaf3bbb5"
DEFAULT_FRONTEND_CLIENT_ID = "f7006176-e51c-4f84-8a89-614ab59dc351"


def _csv_environment(name: str, default: str) -> tuple[str, ...]:
    return tuple(
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    )


def _validate_uuid(name: str, value: str) -> str:
    try:
        UUID(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid UUID") from exc
    return value


@dataclass(frozen=True)
class Settings:
    """Store validated runtime and Microsoft Entra configuration."""

    database_url: str
    entra_tenant_id: str
    entra_api_client_id: str
    entra_api_app_id_uri: str
    entra_allowed_client_ids: tuple[str, ...]
    entra_accepted_scopes: frozenset[str]
    entra_allowed_token_versions: frozenset[str]
    entra_clock_skew_seconds: int

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load and validate application settings from environment variables."""
        tenant_id = _validate_uuid(
            "ENTRA_TENANT_ID",
            os.getenv("ENTRA_TENANT_ID", DEFAULT_TENANT_ID).strip(),
        )
        api_client_id = _validate_uuid(
            "ENTRA_API_CLIENT_ID",
            os.getenv("ENTRA_API_CLIENT_ID", DEFAULT_API_CLIENT_ID).strip(),
        )
        allowed_client_ids = _csv_environment(
            "ENTRA_ALLOWED_CLIENT_IDS", DEFAULT_FRONTEND_CLIENT_ID
        )
        for client_id in allowed_client_ids:
            _validate_uuid("ENTRA_ALLOWED_CLIENT_IDS", client_id)

        accepted_scopes = frozenset(
            _csv_environment("ENTRA_ACCEPTED_SCOPES", "dev-web-app")
        )
        if not accepted_scopes:
            raise ValueError("ENTRA_ACCEPTED_SCOPES must contain at least one scope")

        token_versions = frozenset(
            _csv_environment("ENTRA_ALLOWED_TOKEN_VERSIONS", "1.0,2.0")
        )
        if not token_versions or not token_versions.issubset({"1.0", "2.0"}):
            raise ValueError(
                "ENTRA_ALLOWED_TOKEN_VERSIONS can contain only 1.0 and 2.0"
            )

        clock_skew_seconds = int(os.getenv("ENTRA_CLOCK_SKEW_SECONDS", "60"))
        if not 0 <= clock_skew_seconds <= 300:
            raise ValueError("ENTRA_CLOCK_SKEW_SECONDS must be between 0 and 300")

        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite:///./app.db").strip(),
            entra_tenant_id=tenant_id,
            entra_api_client_id=api_client_id,
            entra_api_app_id_uri=os.getenv(
                "ENTRA_API_APP_ID_URI", f"api://{api_client_id}"
            ).strip(),
            entra_allowed_client_ids=allowed_client_ids,
            entra_accepted_scopes=accepted_scopes,
            entra_allowed_token_versions=token_versions,
            entra_clock_skew_seconds=clock_skew_seconds,
        )

    def issuer(self, token_version: str) -> str:
        """Return the expected Entra token issuer for a token version."""
        if token_version == "2.0":
            return (
                "https://login.microsoftonline.com/"
                f"{self.entra_tenant_id}/v2.0"
            )
        return f"https://sts.windows.net/{self.entra_tenant_id}/"

    def jwks_uri(self, token_version: str) -> str:
        """Return the Entra signing-key endpoint for a token version."""
        suffix = "discovery/v2.0/keys" if token_version == "2.0" else "discovery/keys"
        return f"https://login.microsoftonline.com/{self.entra_tenant_id}/{suffix}"

    def audiences(self, token_version: str) -> tuple[str, ...]:
        """Return accepted token audiences for a token version."""
        if token_version == "2.0":
            return (self.entra_api_client_id,)
        return (self.entra_api_app_id_uri, self.entra_api_client_id)


settings = Settings.from_environment()
