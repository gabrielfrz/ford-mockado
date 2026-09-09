"""Regression tests for the generated OpenAPI contract."""

import unittest

from app.main import app


class OpenApiContractTests(unittest.TestCase):
    """Verify project-specific requirements in the generated API contract."""

    def test_hir_optional_parameters_have_no_prefilled_values(self) -> None:
        """Leave optional HIR filters empty in interactive API documentation."""

        operation = app.openapi()["paths"][
            "/api/v1/fede-status/hir-completion"
        ]["get"]
        parameters = {
            parameter["name"]: parameter
            for parameter in operation["parameters"]
        }

        self.assertIn("example", parameters["gi_code"])
        for name in ("cpsc", "pmt_code", "milestone_date", "dvp_team"):
            self.assertNotIn("example", parameters[name])
            self.assertNotIn("x-42c-sample", parameters[name]["schema"])


if __name__ == "__main__":
    unittest.main()