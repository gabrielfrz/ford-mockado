"""OpenAPI metadata shared by Swagger UI, ReDoc, and API catalogs."""

import os
import re
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute
from app.core.config import settings

API_TITLE = "D&R Dashboard API"
API_VERSION = os.getenv("API_VERSION", "0.1.0")
API_DESCRIPTION = """
API for the D&R Dashboard, providing engineering program data, vehicle-line
information, FEDE status, cost metrics, milestone readiness, and exports.

This API is intended for authorized Ford internal consumers and is protected by
the corporate OAuth 2.0 authorization service at the deployment gateway.
""".strip()

DEFAULT_OPENAPI_SERVER_URL = "/"
OAUTH2_SCHEME_NAME = "CorporateOAuth2"
OAUTH2_AUTHORIZATION_URL = os.getenv(
    "OPENAPI_OAUTH2_AUTHORIZATION_URL",
    f"https://login.microsoftonline.com/{settings.entra_tenant_id}/oauth2/v2.0/authorize",
).strip()
OAUTH2_TOKEN_URL = os.getenv(
    "OPENAPI_OAUTH2_TOKEN_URL",
    f"https://login.microsoftonline.com/{settings.entra_tenant_id}/oauth2/v2.0/token",
).strip()
OAUTH2_SCOPE = os.getenv(
    "OPENAPI_OAUTH2_SCOPE",
    f"{settings.entra_api_app_id_uri}/dev-web-app",
).strip()

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MILESTONE_FIELDS = (
    "mr", "ps", "psc", "fpd", "fc1", "fc2", "fc3", "fc4", "fc5", "k3",
    "k5", "upv0", "upv1", "upv2", "pa", "fdj", "dcv", "pec", "fec", "lr",
    "ls", "j1", "oktb", "fsr", "faa", "ept", "ept_ipd", "tt_ipd", "tt",
    "pp", "mp1", "mp2", "_pcf1", "_tcb1", "_tcb2", "tmr", "tps", "tsc",
    "tdc", "ttc", "tdj", "tpv", "unv0", "unv1", "unv2", "xm", "aa1",
    "vp", "_dtm",
)

OPENAPI_TAGS = [
    {
        "name": "System",
        "description": "API availability and catalog integration operations.",
    },
    {
        "name": "Summary",
        "description": "Consolidated D&R dashboard summaries.",
    },
    {
        "name": "Vehicle Line",
        "description": "Vehicle-line details and program search options.",
    },
    {
        "name": "Effective Point",
        "description": "Effective-point lookup operations.",
    },
    {
        "name": "FEDE Status",
        "description": "FEDE assessments, classifications, and status metrics.",
    },
    {
        "name": "Milestone Readiness",
        "description": "Program milestone-readiness metrics.",
    },
    {
        "name": "DVP Glidepath",
        "description": "DVP glidepath metrics and supporting filters.",
    },
    {
        "name": "Cost Metrics",
        "description": "Tooling, piece-cost, and combined cost metrics.",
    },
    {
        "name": "DPA5",
        "description": "DPA5 records, summaries, and CPSC filters.",
    },
    {
        "name": "PMT",
        "description": "Standard PMT code lookup operations.",
    },
    {
        "name": "Export",
        "description": "Excel exports generated from dashboard data.",
    },
]


def get_openapi_contact() -> dict[str, str]:
    """Return catalog ownership metadata, allowing deployment overrides."""
    contact = {
        "name": os.getenv("OPENAPI_CONTACT_NAME", "D&R Dashboard Team").strip()
        or "D&R Dashboard Team"
    }
    email = os.getenv("OPENAPI_CONTACT_EMAIL", "spiropo@ford.com").strip()
    if email:
        contact["email"] = email
    return contact


def get_openapi_servers() -> list[dict[str, str]]:
    """Build OpenAPI servers from comma-separated deployment URLs."""
    configured_urls = os.getenv(
        "OPENAPI_SERVER_URLS", DEFAULT_OPENAPI_SERVER_URL
    ).split(",")
    urls = [url.strip().rstrip("/") for url in configured_urls if url.strip()]
    if not urls:
        urls = [DEFAULT_OPENAPI_SERVER_URL]

    return [
        {
            "url": url or "/",
            "description": (
                "Current API host"
                if url == ""
                else "Configured environment"
                if len(urls) == 1
                else f"Configured environment {index}"
            ),
        }
        for index, url in enumerate(urls, start=1)
    ]


def generate_operation_id(route: APIRoute) -> str:
    """Generate deterministic, catalog-friendly operation identifiers."""
    method = min(route.methods or {"GET"}).lower()
    normalized_path = re.sub(r"[^a-zA-Z0-9]+", "_", route.path_format).strip("_")
    return f"{method}_{normalized_path}" if normalized_path else method


def _convert_nullable_schemas(value: Any) -> None:
    """Convert JSON Schema null unions to OpenAPI 3.0 nullable schemas."""
    if isinstance(value, list):
        for item in value:
            _convert_nullable_schemas(item)
        return

    if not isinstance(value, dict):
        return

    any_of = value.get("anyOf")
    if isinstance(any_of, list):
        non_null_schemas = [
            schema
            for schema in any_of
            if not (isinstance(schema, dict) and schema.get("type") == "null")
        ]
        if non_null_schemas and len(non_null_schemas) != len(any_of):
            if len(non_null_schemas) == 1:
                nullable_schema = non_null_schemas[0]
                del value["anyOf"]
                if isinstance(nullable_schema, dict) and "$ref" in nullable_schema:
                    value["allOf"] = [nullable_schema]
                elif isinstance(nullable_schema, dict):
                    for key, item in nullable_schema.items():
                        value.setdefault(key, item)
            else:
                value["anyOf"] = non_null_schemas
            value["nullable"] = True

    for item in value.values():
        _convert_nullable_schemas(item)


def _bounded_string_pattern(min_length: int, max_length: int) -> str:
    return rf"^[\s\S]{{{min_length},{max_length}}}$"


def _string_schema(*, min_length: int = 0, max_length: int = 256) -> dict[str, Any]:
    return {
        "type": "string",
        "minLength": min_length,
        "maxLength": max_length,
        "pattern": _bounded_string_pattern(min_length, max_length),
    }


def _integer_schema(*, minimum: int = 0, maximum: int = 2_147_483_647) -> dict[str, Any]:
    return {
        "type": "integer",
        "format": "int32",
        "minimum": minimum,
        "maximum": maximum,
    }


def _number_schema(*, minimum: float = -1_000_000_000_000.0, maximum: float = 1_000_000_000_000.0) -> dict[str, Any]:
    return {
        "type": "number",
        "format": "double",
        "minimum": minimum,
        "maximum": maximum,
    }


def _array_schema(items: dict[str, Any], *, max_items: int = 10_000) -> dict[str, Any]:
    return {
        "type": "array",
        "maxItems": max_items,
        "items": items,
    }


def _object_schema(
    properties: dict[str, Any],
    *,
    required: tuple[str, ...] = (),
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "maxProperties": max(len(properties), 1),
        "properties": properties,
    }
    if required:
        schema["required"] = list(required)
    return schema


def _row_array() -> dict[str, Any]:
    return _array_schema({"$ref": "#/components/schemas/DynamicDataRow"})


def _string_array() -> dict[str, Any]:
    return _array_schema(_string_schema())


def _success_response_schemas() -> dict[str, dict[str, Any]]:
    string = _string_schema()
    integer = _integer_schema()
    number = _number_schema()
    optional_message = _string_schema(max_length=4096)
    return {
        "/vehicle-line/": {"$ref": "#/components/schemas/VehicleLineSchema"},
        "/search/model-years": _string_array(),
        "/search/program-names": _string_array(),
        "/search/program-codes": _string_array(),
        "/effective-point/": _array_schema(
            _object_schema(
                {"id": integer, "effective_point": string, "status": string},
                required=("id", "effective_point", "status"),
            )
        ),
        "/effective-point/search/": _object_schema(
            {"effective_point": string, "exists": {"type": "boolean"}},
            required=("effective_point", "exists"),
        ),
        "/fede-status/dvp-teams/autocomplete": _object_schema(
            {"dvp_teams": _string_array(), "count": integer},
            required=("dvp_teams", "count"),
        ),
        "/fede-status/dvp-teams/autocomplete/by-gi-code": _object_schema(
            {"gi_code": string, "dvp_teams": _string_array(), "count": integer, "message": optional_message},
            required=("gi_code", "dvp_teams", "count"),
        ),
        "/fede-status/cpsc/list": _object_schema(
            {"gi_code": string, "cpsc_codes": _string_array(), "count": integer},
            required=("gi_code", "cpsc_codes", "count"),
        ),
        "/fede-status/cpsc/autocomplete": _object_schema(
            {"gi_code": string, "cpsc_codes": _string_array(), "count": integer, "message": optional_message},
            required=("gi_code", "cpsc_codes", "count"),
        ),
        "/fede-status/metrics/dvp-team-list": _object_schema(
            {"gi_code": string, "dvp_teams_metrics": _row_array(), "total_teams": integer},
            required=("gi_code", "dvp_teams_metrics", "total_teams"),
        ),
        "/fede-status/metrics/total-assessments": _object_schema(
            {"total_assessments": integer, "gi_code": string},
            required=("total_assessments",),
        ),
        "/fede-status/metrics/conf-state": _object_schema(
            {
                "Meet": integer,
                "Does Not Meet": integer,
                "Unassessed": integer,
                "Approved Deviation": integer,
                "Cannot Assess": integer,
                "Not Applicable": integer,
            }
        ),
        "/fede-status/metrics/assessment-dvp-status": _object_schema(
            {"gi_code": string, "data": _row_array()}, required=("gi_code", "data")
        ),
        "/fede-status/metrics/design-rules-evidences": _object_schema(
            {"gi_code": string, "design_rules_evidences": _row_array(), "total": integer},
            required=("gi_code", "design_rules_evidences", "total"),
        ),
        "/fede-status/metrics/dr-evidences-by-assessment": _object_schema(
            {"gi_code": string, "cpsc": string, "dr_evidences": _row_array()},
            required=("gi_code", "dr_evidences"),
        ),
        "/fede-status/metrics/cae-graph": _object_schema(
            {"gi_code": string, "cae_data": _row_array()}, required=("gi_code", "cae_data")
        ),
        "/fede-status/metrics/design-rule-classification": _object_schema(
            {"model_year": string, "program_name": string, "classifications": {"$ref": "#/components/schemas/DynamicDataRow"}},
            required=("model_year", "program_name", "classifications"),
        ),
        "/fede-status/metrics/cae-total-assessments": _object_schema(
            {"gi_code": string, "program": string, "cpsc": string, "total_assessments": integer},
            required=("gi_code", "total_assessments"),
        ),
        "/fede-status/metrics/cae-detailed": _object_schema(
            {"gi_code": string, "program": string, "cae_records": _row_array()},
            required=("gi_code", "cae_records"),
        ),
        "/api/v1/fede-status/dvp-classification": _object_schema(
            {"gi_code": string, "cpsc": string, "total": integer, "classified": integer, "unclassified": integer, "percentage": number},
            required=("gi_code", "cpsc", "total", "classified", "unclassified", "percentage"),
        ),
        "/api/v1/fede-status/hir-completion": _object_schema(
            {"gi_code": string, "cpsc": string, "pmt_code": string, "milestone_date": string, "hir_metrics": {"$ref": "#/components/schemas/DynamicDataRow"}},
            required=("gi_code", "hir_metrics"),
        ),
        "/api/v1/milestone-readiness/{gi_code}": _object_schema(
            {"gi_code": string, "program": string, "milestone": string, "milestone_date": string, "metrics": _row_array()},
            required=("gi_code", "program", "milestone", "metrics"),
        ),
        "/cost/cpsc/list": _object_schema(
            {"effectivein": string, "cpsc_codes": _string_array(), "count": integer},
            required=("effectivein", "cpsc_codes", "count"),
        ),
        "/cost/cpsc/autocomplete": _object_schema(
            {"effectivein": string, "cpsc_codes": _string_array(), "count": integer, "message": optional_message},
            required=("effectivein", "cpsc_codes", "count"),
        ),
        "/cost/pmt/list": _object_schema(
            {"effectivein": string, "cpsc": string, "pmt_list": _string_array(), "count": integer},
            required=("effectivein", "pmt_list", "count"),
        ),
        "/cost/dropdowns": _object_schema(
            {"effectivein": string, "partnumbers": _string_array(), "commodities": _row_array(), "vehicle_lines": _string_array()},
            required=("effectivein", "partnumbers", "commodities", "vehicle_lines"),
        ),
        "/cost/partnumber/list": _object_schema(
            {"effectivein": string, "partnumbers": _string_array(), "count": integer},
            required=("effectivein", "partnumbers", "count"),
        ),
        "/cost/commodity/list": _object_schema(
            {"effectivein": string, "commodities": _row_array(), "count": integer},
            required=("effectivein", "commodities", "count"),
        ),
        "/cost/vehicleline/list": _object_schema(
            {"effectivein": string, "vehicle_lines": _string_array(), "count": integer},
            required=("effectivein", "vehicle_lines", "count"),
        ),
        "/cost/metrics/tooling": _object_schema(
            {"effectivein": string, "cpsc": string, "pmt_code": string, "tooling_metrics": _row_array()},
            required=("effectivein", "tooling_metrics"),
        ),
        "/cost/metrics/piece": _object_schema(
            {"effectivein": string, "partnumber": string, "cpsc": string, "pmt_code": string, "piece_metrics": _row_array()},
            required=("effectivein", "piece_metrics"),
        ),
        "/cost/metrics/combined": _object_schema(
            {"effectivein": string, "cpsc": string, "pmt_code": string, "tooling": {"$ref": "#/components/schemas/DynamicDataRow"}, "piece": {"$ref": "#/components/schemas/DynamicDataRow"}, "summary": {"$ref": "#/components/schemas/DynamicDataRow"}},
            required=("effectivein", "tooling", "piece", "summary"),
        ),
        "/api/v1/dvp-glidepath/data": _object_schema(
            {"gi_code": string, "pmt": string, "milestone": string, "data": _row_array(), "total_records": integer},
            required=("gi_code", "data", "total_records"),
        ),
        "/api/v1/dvp-glidepath/pmts": _object_schema(
            {"gi_code": string, "pmts": _string_array(), "total": integer},
            required=("gi_code", "pmts", "total"),
        ),
        "/api/v1/dvp-glidepath/milestones": _object_schema(
            {"gi_code": string, "pmt": string, "milestones": _string_array(), "total": integer},
            required=("gi_code", "milestones", "total"),
        ),
        "/pmt/list": _object_schema(
            {"pmt_codes": _string_array(), "mapping": {"$ref": "#/components/schemas/DynamicDataRow"}, "count": integer},
            required=("pmt_codes", "mapping", "count"),
        ),
        "/dpa5/data": _object_schema(
            {"gi_code": string, "cpsc_filter": string, "pmt_filter": string, "data": _row_array(), "page": integer, "limit": integer, "total_records": integer, "total_pages": integer},
            required=("gi_code", "data", "page", "limit", "total_records", "total_pages"),
        ),
        "/dpa5/summary": _object_schema(
            {"gi_code": string, "cpsc_filter": string, "pmt_filter": string, "summary": {"$ref": "#/components/schemas/DynamicDataRow"}, "glidepath_goals": _row_array()},
            required=("gi_code", "summary", "glidepath_goals"),
        ),
        "/dpa5/cpsc-list": _object_schema(
            {"gi_code": string, "pmt_filter": string, "cpsc_codes": _string_array(), "count": integer},
            required=("gi_code", "cpsc_codes", "count"),
        ),
    }


def _add_common_components(schema: dict[str, Any]) -> None:
    components = schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    effective_point_schema = _object_schema(
        {"effective_point": _string_schema()}, required=("effective_point",)
    )
    summary_schema = schemas.get("SummarySchema")
    if isinstance(summary_schema, dict):
        summary_properties = summary_schema.get("properties", {})
        if isinstance(summary_properties, dict):
            summary_properties["effective_point"] = effective_point_schema
    vehicle_line_schema = schemas.get("VehicleLineSchema")
    if isinstance(vehicle_line_schema, dict):
        vehicle_properties = vehicle_line_schema.get("properties", {})
        if isinstance(vehicle_properties, dict):
            vehicle_properties["effective_point"] = {
                **effective_point_schema,
                "nullable": True,
            }
            vehicle_properties["milestones"] = {
                **_object_schema(
                    {
                        field: {**_string_schema(), "nullable": True}
                        for field in MILESTONE_FIELDS
                    }
                ),
                "nullable": True,
            }
    schemas["ApiError"] = _object_schema(
        {"detail": _string_schema(max_length=4096)}, required=("detail",)
    )
    schemas["DynamicDataRow"] = {
        "type": "object",
        "minProperties": 0,
        "maxProperties": 256,
        "additionalProperties": {
            "oneOf": [
                _string_schema(max_length=4096),
                _number_schema(),
                _integer_schema(minimum=-2_147_483_648),
                {"type": "boolean"},
                {
                    "type": "array",
                    "maxItems": 10_000,
                    "items": {
                        "oneOf": [
                            _string_schema(max_length=4096),
                            _number_schema(),
                            _integer_schema(minimum=-2_147_483_648),
                            {"type": "boolean"},
                        ]
                    },
                },
            ]
        },
    }
    components["securitySchemes"] = {
        OAUTH2_SCHEME_NAME: {
            "type": "oauth2",
            "description": "Corporate OAuth 2.0 authorization-code flow.",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": OAUTH2_AUTHORIZATION_URL,
                    "tokenUrl": OAUTH2_TOKEN_URL,
                    "scopes": {OAUTH2_SCOPE: "Access the D&R Dashboard API"},
                }
            },
        }
    }
    error_content = {
        "application/json": {"schema": {"$ref": "#/components/schemas/ApiError"}}
    }
    components["responses"] = {
        "BadRequest": {"description": "Invalid request", "content": error_content},
        "Unauthorized": {"description": "OAuth 2.0 access token is missing or invalid", "content": error_content},
        "Forbidden": {"description": "The authenticated identity is not authorized", "content": error_content},
        "NotFound": {"description": "Requested resource was not found", "content": error_content},
        "NotAcceptable": {"description": "Requested representation is not available", "content": error_content},
        "TooManyRequests": {"description": "Request rate limit exceeded", "content": error_content},
        "ServerError": {"description": "Unexpected server error", "content": error_content},
        "DefaultError": {"description": "Unexpected error", "content": error_content},
    }


def _parameter_example(parameter: dict[str, Any]) -> Any:
    name = str(parameter.get("name", ""))
    parameter_schema = parameter.get("schema", {})
    if parameter_schema.get("default") not in (None, ""):
        return parameter_schema["default"]
    examples: dict[str, Any] = {
        "gi_code": "GI-10001",
        "gi_id": "GI-10001",
        "cpsc": "12A45",
        "effectivein": "S4PVBS",
        "pmt": "200",
        "pmt_code": "200",
        "model_year": "2027",
        "program_code": "U725",
        "program_codes": "U725",
        "program_name": "Bronco",
        "program_names": "Bronco",
        "partnumber": "S2DB-19A497-RCAW",
        "milestone": "mr",
        "milestone_date": "2027-03-15",
        "code": "S4PVBS",
        "q": "12A",
        "query": "Bronco",
        "page": 1,
        "limit": 100,
        "selected_index": 0,
    }
    value = examples.get(name, "sample")
    schema_type = parameter_schema.get("type")
    if schema_type == "integer":
        return int(value) if isinstance(value, (int, float, str)) and str(value).isdigit() else 1
    if schema_type == "number":
        try:
            return float(value)
        except (TypeError, ValueError):
            return 1.0
    return str(value)


def _harden_schema(value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            _harden_schema(item)
        return
    if not isinstance(value, dict):
        return

    schema_type = value.get("type")
    if schema_type == "string" and value.get("format") != "binary":
        min_length = value.setdefault("minLength", 0)
        max_length = value.setdefault("maxLength", 256)
        value.setdefault(
            "pattern", _bounded_string_pattern(min_length, max_length)
        )
    elif schema_type == "integer":
        value.setdefault("format", "int32")
        value.setdefault("minimum", -2_147_483_648)
        value.setdefault("maximum", 2_147_483_647)
    elif schema_type == "number":
        value.setdefault("format", "double")
        value.setdefault("minimum", -1_000_000_000_000.0)
        value.setdefault("maximum", 1_000_000_000_000.0)
    elif schema_type == "array":
        value.setdefault("maxItems", 10_000)
    elif schema_type == "object" and "properties" in value:
        value.setdefault("additionalProperties", False)
        value.setdefault("maxProperties", max(len(value["properties"]), 1))

    for item in value.values():
        _harden_schema(item)


def _harden_operations(schema: dict[str, Any]) -> None:
    success_schemas = _success_response_schemas()
    security_requirement = [{OAUTH2_SCHEME_NAME: [OAUTH2_SCOPE]}]
    standard_responses = {
        "400": {"$ref": "#/components/responses/BadRequest"},
        "401": {"$ref": "#/components/responses/Unauthorized"},
        "403": {"$ref": "#/components/responses/Forbidden"},
        "404": {"$ref": "#/components/responses/NotFound"},
        "406": {"$ref": "#/components/responses/NotAcceptable"},
        "429": {"$ref": "#/components/responses/TooManyRequests"},
        "500": {"$ref": "#/components/responses/ServerError"},
        "default": {"$ref": "#/components/responses/DefaultError"},
    }

    for path, path_item in schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            if path == "/test":
                operation["security"] = []
                operation["x-42c-no-authentication"] = True
            else:
                operation["security"] = security_requirement
            for parameter in operation.get("parameters", []):
                if not isinstance(parameter, dict):
                    continue
                is_optional_hir_parameter = (
                    path == "/api/v1/fede-status/hir-completion"
                    and not parameter.get("required", False)
                )
                if is_optional_hir_parameter:
                    parameter.pop("example", None)
                    parameter_schema = parameter.get("schema")
                    if isinstance(parameter_schema, dict):
                        parameter_schema.pop("x-42c-sample", None)
                    continue
                example = _parameter_example(parameter)
                parameter.setdefault("example", example)
                parameter_schema = parameter.get("schema")
                if isinstance(parameter_schema, dict):
                    if parameter.get("required") and parameter_schema.get("type") == "string":
                        min_length = max(parameter_schema.get("minLength", 0), 1)
                        max_length = parameter_schema.get("maxLength", 256)
                        parameter_schema["minLength"] = min_length
                        parameter_schema.setdefault(
                            "pattern",
                            _bounded_string_pattern(min_length, max_length),
                        )
                    parameter_schema.setdefault("x-42c-sample", example)

            responses = operation.setdefault("responses", {})
            for status_code, response in standard_responses.items():
                responses.setdefault(status_code, response)

            if path.startswith("/export/"):
                responses["200"] = {
                    "description": "Excel workbook",
                    "headers": {
                        "Content-Disposition": {
                            "description": "Attachment filename",
                            "schema": _string_schema(),
                        }
                    },
                    "content": {
                        EXCEL_MEDIA_TYPE: {
                            "schema": {"type": "string", "format": "binary"}
                        }
                    },
                }
                continue

            response_schema = success_schemas.get(path)
            success_response = responses.get("200")
            if response_schema and isinstance(success_response, dict):
                content = success_response.setdefault("content", {})
                media_type = content.setdefault("application/json", {})
                current_schema = media_type.get("schema")
                if not current_schema:
                    media_type["schema"] = response_schema


def _harden_openapi_schema(schema: dict[str, Any]) -> None:
    _add_common_components(schema)
    schema["security"] = [{OAUTH2_SCHEME_NAME: [OAUTH2_SCOPE]}]
    _harden_operations(schema)
    _harden_schema(schema)


def configure_openapi_compatibility(app: FastAPI) -> None:
    """Install OpenAPI 3.0 compatibility normalization on the application."""
    default_openapi = app.openapi

    def custom_openapi() -> dict[str, Any]:
        schema = default_openapi()
        _convert_nullable_schemas(schema)
        _harden_openapi_schema(schema)
        return schema

    app.openapi = custom_openapi
