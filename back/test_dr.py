import os
from app.services.bigquery_client import get_client

client = get_client()
df = client.query(f'SELECT * FROM `{client.project}.DANDR_DEV.dr_design_rule` LIMIT 1').to_dataframe()
print(df.columns.tolist())
