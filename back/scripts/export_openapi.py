"""Export the FastAPI OpenAPI contract as deterministic JSON."""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse the destination path for the generated OpenAPI contract."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "openapi.json",
        help="Destination file (default: <project>/openapi.json)",
    )
    return parser.parse_args()


def export_openapi(output: Path) -> Path:
    """Write the current application contract atomically."""
    schema = app.openapi()
    if schema.get("openapi") != "3.0.3":
        raise ValueError("The 42Crunch contract must use OpenAPI 3.0.3")

    destination = output.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(f"{destination.suffix}.tmp")
    temporary.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination


def main() -> None:
    """Export the current application contract and print a short summary."""
    args = parse_args()
    destination = export_openapi(args.output)
    schema = app.openapi()
    print(
        f"Generated {destination} "
        f"({schema['openapi']}, {len(schema['paths'])} paths)"
    )


if __name__ == "__main__":
    main()
