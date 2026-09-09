"""Expose canonical PMT codes shared by all deliverable modules."""

from fastapi import APIRouter

router = APIRouter(prefix="/pmt", tags=["PMT"])

PMT_CODES = ["100", "200", "300", "400", "500", "600"]

# Map canonical PMT codes to source-specific values for each deliverable.
# Add an entry whenever another source uses a different naming convention.
PMT_CODE_MAP: dict[str, dict[str, str]] = {
    "100": {"cost": "1"},
    "200": {"cost": "2"},
    "300": {"cost": "3"},
    "400": {"cost": "4"},
    "500": {"cost": "5"},
    "600": {"cost": "6"},
}


def resolve_pmt(pmt_display: str, module: str) -> str | None:
    """Resolve a canonical PMT code to a module-specific source value."""
    return PMT_CODE_MAP.get(pmt_display, {}).get(module)


@router.get("/list", summary="List canonical PMT codes")
def list_pmt_codes():
    """Return canonical PMT codes and source-specific mappings."""
    return {
        "pmt_codes": PMT_CODES,
        "mapping": PMT_CODE_MAP,
        "count": len(PMT_CODES)
    }
