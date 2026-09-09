"""Microsoft Entra ID bearer-token authentication for protected API routes."""

from dataclasses import dataclass
from functools import lru_cache
import logging
from typing import Any, Mapping

from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError

from app.core.config import Settings, settings

LOGGER = logging.getLogger(__name__)
BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}

bearer_scheme = HTTPBearer(
    auto_error=False,
    bearerFormat="JWT",
    description="Microsoft Entra ID access token for the D&R Dashboard API.",
    scheme_name="CorporateOAuth2",
)


class TokenValidationError(ValueError):
    """Raised when an access token cannot be authenticated."""


class TokenAuthorizationError(PermissionError):
    """Raised when an authenticated token lacks required authorization."""


@dataclass(frozen=True)
class EntraPrincipal:
    """Represent the validated identity and authorization claims of a caller."""

    subject: str
    object_id: str
    tenant_id: str
    client_id: str | None
    scopes: frozenset[str]
    claims: Mapping[str, Any]


@lru_cache(maxsize=4)
def _jwks_client(jwks_uri: str) -> PyJWKClient:
    return PyJWKClient(
        jwks_uri,
        cache_keys=True,
        cache_jwk_set=True,
        lifespan=86_400,
        timeout=5,
    )


def _token_version(token: str, auth_settings: Settings) -> str:
    try:
        unverified_claims = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_exp": False,
            },
        )
    except InvalidTokenError as exc:
        raise TokenValidationError("Malformed access token") from exc

    token_version = unverified_claims.get("ver")
    if token_version not in auth_settings.entra_allowed_token_versions:
        raise TokenValidationError("Unsupported access-token version")
    return str(token_version)


def validate_access_token(
    token: str,
    *,
    auth_settings: Settings = settings,
    signing_key: Any | None = None,
) -> EntraPrincipal:
    """Validate an Entra access token and return its authorization principal."""
    token_version = _token_version(token, auth_settings)

    try:
        key = signing_key
        if key is None:
            key = _jwks_client(
                auth_settings.jwks_uri(token_version)
            ).get_signing_key_from_jwt(token).key

        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=auth_settings.audiences(token_version),
            issuer=auth_settings.issuer(token_version),
            leeway=auth_settings.entra_clock_skew_seconds,
            options={
                "require": [
                    "aud",
                    "exp",
                    "iat",
                    "iss",
                    "nbf",
                    "sub",
                    "tid",
                    "ver",
                ]
            },
        )
    except (InvalidTokenError, PyJWKClientError) as exc:
        raise TokenValidationError("Access-token validation failed") from exc

    if claims.get("tid") != auth_settings.entra_tenant_id:
        raise TokenValidationError("Access token belongs to another tenant")

    object_id = claims.get("oid")
    subject = claims.get("sub")
    if not isinstance(object_id, str) or not isinstance(subject, str):
        raise TokenValidationError("Access token has no stable user subject")

    scopes = frozenset(str(claims.get("scp", "")).split())
    if not scopes.intersection(auth_settings.entra_accepted_scopes):
        raise TokenAuthorizationError("Required delegated scope is missing")

    client_claim = "azp" if token_version == "2.0" else "appid"
    client_id = claims.get(client_claim)
    if auth_settings.entra_allowed_client_ids and (
        not isinstance(client_id, str)
        or client_id not in auth_settings.entra_allowed_client_ids
    ):
        raise TokenAuthorizationError("Client application is not authorized")

    return EntraPrincipal(
        subject=subject,
        object_id=object_id,
        tenant_id=auth_settings.entra_tenant_id,
        client_id=client_id if isinstance(client_id, str) else None,
        scopes=scopes,
        claims=claims,
    )


def require_authenticated_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> EntraPrincipal:
    """FastAPI dependency enforcing an authorized delegated Entra user token."""
    forwarded_authorization = request.headers.get("x-forwarded-authorization", "")
    if forwarded_authorization:
        scheme, separator, token = forwarded_authorization.partition(" ")
        if separator and scheme.lower() == "bearer" and token.strip():
            credentials = HTTPAuthorizationCredentials(
                scheme=scheme,
                credentials=token.strip(),
            )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A Microsoft Entra bearer access token is required",
            headers=BEARER_CHALLENGE,
        )

    try:
        principal = validate_access_token(credentials.credentials)
    except TokenValidationError:
        LOGGER.info("Rejected an invalid Microsoft Entra access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The Microsoft Entra access token is invalid or expired",
            headers=BEARER_CHALLENGE,
        ) from None
    except TokenAuthorizationError:
        LOGGER.info("Rejected a Microsoft Entra token without API authorization")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The access token does not grant access to this API",
        ) from None

    request.state.entra_principal = principal
    return principal