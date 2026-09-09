"""Provide a manual BigQuery connectivity and dataset-listing diagnostic."""

from google.cloud import bigquery

def main():
    """Connect to the configured project and print its available datasets."""
    project_id = "ford-ae4fa4b1aca14194fe8e5c19"

    print("Connecting to BigQuery...")
    client = bigquery.Client(project=project_id)

    datasets = list(client.list_datasets())

    if not datasets:
        print("Connected successfully, but no datasets found.")
        return

    print("\nDatasets in the project:\n")
    for d in datasets:
        print(f"- {d.dataset_id}")

    print("\nBigQuery connection successful!")

if __name__ == "__main__":
    main()
