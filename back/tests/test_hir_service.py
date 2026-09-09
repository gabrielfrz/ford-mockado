"""Regression tests for HIR query construction."""

import unittest
from unittest.mock import patch

import pandas as pd

from app.services import fede_status_service


class _EmptyQueryResult:
    def to_dataframe(self) -> pd.DataFrame:
        """Return an empty query result as a data frame."""

        return pd.DataFrame()


class _CapturingClient:
    project = "test-project"

    def __init__(self) -> None:
        self.sql = ""
        self.job_config = None

    def query(self, sql: str, job_config=None) -> _EmptyQueryResult:
        """Capture query arguments and return an empty result."""

        self.sql = sql
        self.job_config = job_config
        return _EmptyQueryResult()


class HirQueryTests(unittest.TestCase):
    """Verify the relationship keys used to construct the HIR query."""

    def test_joins_hir_assessment_to_status_pk_record(self) -> None:
        """Join HIR assessments through the status primary-key record."""

        client = _CapturingClient()

        with patch.object(fede_status_service, "get_client", return_value=client):
            result = fede_status_service.get_hir_completion_metrics("GI-10032")

        self.assertIn("CAST(pk_rec AS STRING) AS pk4_id", client.sql)
        self.assertIn("st.pk_rec IS NOT NULL", client.sql)
        self.assertNotIn("CAST(pk4_rec AS STRING) AS pk4_id", client.sql)
        self.assertEqual(result["total_records"], 0)


if __name__ == "__main__":
    unittest.main()