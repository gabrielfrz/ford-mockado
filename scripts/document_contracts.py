"""Compatibility entry point for the complete current data documentation."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('document_data_pipeline.py')), run_name='__main__')
