"""Provide centralized BigQuery project, dataset, and table configuration."""

from google.cloud import bigquery

# BigQuery Project Configuration
PROJECT_ID = "ford-ae4fa4b1aca14194fe8e5c19"

# Secondary project for BOM data (if different from main project)
BOM_PROJECT_ID = "prj-dfad-1242-uapd-p-1242"  # Project that hosts the BOM dataset

# Available Datasets
DATASETS = {
    "dandr": {
        "project": PROJECT_ID,
        "dataset": "DANDR_DEV",
        "description": "Primary D&R dataset (vehicle_line, dvp_fede, and related tables)"
    },
    "bom": {
        "project": BOM_PROJECT_ID,
        "dataset": "bq_284_fedebom_lc_vw",
        "description": "BOM dataset for tooling and piece costs"
    }
}

# Frequently used tables
TABLES = {
    # DANDR_DEV tables
    "vehicle_line": "vehicle_line",
    "dvp_fede": "dvp_fede",
    "dr_design_rule": "dr_design_rule",
    "fede_daily_requirementvw": "fede_daily_requirementvw",
    "drassesmentvw": "drassesmentvw",
    "fede_daily_fedestatus": "fede_daily_fedestatus",
    
    # bq_284_fedebom_lc_vw tables
    "bom_load": "pfbrj34_fedebom_r1_ei_r5_c_bom_load_vw",
}


def get_client():
    """Return a BigQuery client configured for the primary project."""
    import os
    if os.getenv("DANDR_ENABLE_BIGQUERY") != "1":
        raise RuntimeError("BigQuery is disabled in this local demo. Use run-demo.sh.")
    client = bigquery.Client(project=PROJECT_ID)
    return client


def get_table_path(dataset_key: str, table_name: str) -> str:
    """Build a fully qualified ``project.dataset.table`` path.

    ``table_name`` may be either a physical table name or a key in ``TABLES``.
    Raises ``ValueError`` when ``dataset_key`` is unknown.
    """
    dataset_config = DATASETS.get(dataset_key)
    if not dataset_config:
        raise ValueError(f"Dataset '{dataset_key}' was not found. Available datasets: {list(DATASETS.keys())}")
    
    # Resolve the project and dataset from the shared configuration.
    project = dataset_config["project"]
    dataset = dataset_config["dataset"]
    
    # Resolve logical table keys while accepting physical names directly.
    actual_table = TABLES.get(table_name, table_name)
    
    return f"{project}.{dataset}.{actual_table}"


def get_dataset_name(dataset_key: str) -> str:
    """Return the physical dataset name for a configured dataset key."""
    dataset_config = DATASETS.get(dataset_key)
    if not dataset_config:
        raise ValueError(f"Dataset '{dataset_key}' was not found. Available datasets: {list(DATASETS.keys())}")
    return dataset_config["dataset"]


def get_dataset_project(dataset_key: str) -> str:
    """Return the project ID that hosts a configured dataset."""
    dataset_config = DATASETS.get(dataset_key)
    if not dataset_config:
        raise ValueError(f"Dataset '{dataset_key}' was not found. Available datasets: {list(DATASETS.keys())}")
    return dataset_config["project"]
