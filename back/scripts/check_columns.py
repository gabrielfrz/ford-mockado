"""Print the BigQuery schema of the DVP FEDE table for diagnostics."""

from app.services.bigquery_client import get_client
client = get_client()
q = "SELECT column_name, data_type FROM `ford-ae4fa4b1aca14194fe8e5c19.DANDR_DEV.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = 'dvp_fede' ORDER BY ordinal_position"
df = client.query(q).to_dataframe()
print(df.to_string())
