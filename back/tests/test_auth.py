"""Unit tests for Microsoft Entra access-token validation."""

import time
import unittest

from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

from app.core.auth import (
    TokenAuthorizationError,
    TokenValidationError,
    validate_access_token,
)
from app.core.config import Settings

TENANT_ID = "c990bb7a-51f4-439b-bd36-9c07fb1041c0"
API_CLIENT_ID = "e78c1e61-6047-47ed-8e6a-3a5ddaf3bbb5"
FRONTEND_CLIENT_ID = "f7006176-e51c-4f84-8a89-614ab59dc351"


class EntraTokenValidationTests(unittest.TestCase):
    """Verify acceptance and rejection rules for Microsoft Entra tokens."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create signing keys and strict authentication settings for the suite."""

        cls.private_key = rsa.generate_private_key(
            public_exponent=65_537,
            key_size=2_048,
        )
        cls.public_key = cls.private_key.public_key()
        cls.settings = Settings(
            database_url="sqlite:///./app.db",
            entra_tenant_id=TENANT_ID,
            entra_api_client_id=API_CLIENT_ID,
            entra_api_app_id_uri=f"api://{API_CLIENT_ID}",
            entra_allowed_client_ids=(FRONTEND_CLIENT_ID,),
            entra_accepted_scopes=frozenset({"dev-web-app"}),
            entra_allowed_token_versions=frozenset({"1.0", "2.0"}),
            entra_clock_skew_seconds=0,
        )

    def issue_token(self, version: str = "2.0", **overrides: object) -> str:
        """Issue a signed test token with optional claim overrides."""

        now = int(time.time())
        claims: dict[str, object] = {
            "aud": (
                API_CLIENT_ID if version == "2.0" else f"api://{API_CLIENT_ID}"
            ),
            "exp": now + 300,
            "iat": now,
            "iss": self.settings.issuer(version),
            "nbf": now,
            "oid": "11111111-2222-3333-4444-555555555555",
            "scp": "dev-web-app",
            "sub": "test-user-subject",
            "tid": TENANT_ID,
            "ver": version,
            "azp" if version == "2.0" else "appid": FRONTEND_CLIENT_ID,
        }
        claims.update(overrides)
        return jwt.encode(claims, self.private_key, algorithm="RS256")

    def validate(self, token: str):
        """Validate a token using the suite's settings and public key."""

        return validate_access_token(
            token,
            auth_settings=self.settings,
            signing_key=self.public_key,
        )

    def test_accepts_authorized_v2_delegated_token(self) -> None:
        """Accept an authorized version 2 delegated access token."""

        principal = self.validate(self.issue_token())

        self.assertEqual(principal.tenant_id, TENANT_ID)
        self.assertEqual(principal.client_id, FRONTEND_CLIENT_ID)
        self.assertIn("dev-web-app", principal.scopes)

    def test_accepts_authorized_v1_delegated_token(self) -> None:
        """Accept an authorized version 1 delegated access token."""

        principal = self.validate(self.issue_token("1.0"))

        self.assertEqual(principal.client_id, FRONTEND_CLIENT_ID)

    def test_rejects_token_for_another_audience(self) -> None:
        """Reject a token issued for an unrelated audience."""

        with self.assertRaises(TokenValidationError):
            self.validate(self.issue_token(aud="00000000-0000-0000-0000-000000000000"))

    def test_rejects_expired_token(self) -> None:
        """Reject a token whose expiration time has passed."""

        with self.assertRaises(TokenValidationError):
            self.validate(self.issue_token(exp=int(time.time()) - 1))

    def test_rejects_token_from_another_tenant(self) -> None:
        """Reject a token issued by a tenant that is not configured."""

        with self.assertRaises(TokenValidationError):
            self.validate(
                self.issue_token(
                    iss=(
                        "https://login.microsoftonline.com/"
                        "00000000-0000-0000-0000-000000000000/v2.0"
                    ),
                    tid="00000000-0000-0000-0000-000000000000",
                )
            )

    def test_rejects_token_signed_by_another_key(self) -> None:
        """Reject a token whose signature does not match the trusted key."""

        other_key = rsa.generate_private_key(public_exponent=65_537, key_size=2_048)
        token = jwt.encode(
            jwt.decode(self.issue_token(), options={"verify_signature": False}),
            other_key,
            algorithm="RS256",
        )

        with self.assertRaises(TokenValidationError):
            self.validate(token)

    def test_rejects_token_without_object_id(self) -> None:
        """Reject a token that does not identify the user object."""

        with self.assertRaises(TokenValidationError):
            self.validate(self.issue_token(oid=None))

    def test_rejects_token_without_required_scope(self) -> None:
        """Reject a token that lacks an accepted delegated scope."""

        with self.assertRaises(TokenAuthorizationError):
            self.validate(self.issue_token(scp="User.Read"))

    def test_rejects_unapproved_client_application(self) -> None:
        """Reject a token issued to an unapproved client application."""

        with self.assertRaises(TokenAuthorizationError):
            self.validate(
                self.issue_token(azp="00000000-0000-0000-0000-000000000000")
            )


if __name__ == "__main__":
    unittest.main()