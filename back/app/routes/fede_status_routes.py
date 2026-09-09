"""Expose DVP, CAE, Design Rule, and HIR status metrics."""

from fastapi import APIRouter, Query, HTTPException
from app.services.fede_status_service import (
    get_metrics_by_dvp_team_list,
    get_dvp_teams_by_gi_code,
    autocomplete_dvp_team_by_gi_code,
    autocomplete_dvp_team,
    count_total_assessments,
    count_conf_state_results,
    get_assessment_dvp_status,
    get_design_rules_evidences_metrics,
    get_cae_graph_data,
    get_design_rule_classification,
    get_cae_total_assessments,
    get_cae_detailed_data,
    get_cpsc_by_gi_code,
    autocomplete_cpsc_by_gi_code,
    get_dr_evidences_by_assessment,
    get_dvp_classification_metrics,
    get_hir_completion_metrics
)

router = APIRouter(prefix="/fede-status", tags=["FEDE Status"])
router_v1 = APIRouter(prefix="/api/v1/fede-status", tags=["FEDE Status"])

@router_v1.get("/dvp-classification", summary="DVP classification metrics", description="Return total, classified, unclassified, and percentage values for a GI code and CPSC.")
def dvp_classification(
    gi_code: str = Query(..., description="GI Code do vehicle_line"),
    cpsc: str = Query(..., description="Commodity CPSC"),
    snapshot_date: str = Query(None, description="Snapshot date opcional")
):
    """Return DVP requirement-classification metrics."""
    try:
        return get_dvp_classification_metrics(gi_code, cpsc, snapshot_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate classification metrics: {str(e)}")

@router.get("/dvp-teams/autocomplete", summary="Autocomplete DVP teams by GI code", description="Return DVP team suggestions filtered by GI code.")
def autocomplete_dvp_teams(
    gi_code: str = Query(..., description="Vehicle-line GI code"),
    q: str = Query("", description="DVP team search term"),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Execute DVP team autocomplete search filtered by GI code.
    
    Args:
        gi_code: GI Code for filtering results (required)
        q: Search term for filtering DVP team names (case-insensitive)
    
    Metrics:
        - dvp_teams: List of matching DVP team values
        - count: Total count of results
    
    Rules:
        - Returns ONLY DVP teams belonging to the specified gi_code
        - Case-insensitive matching using LIKE operator
        - Returns unique values only
        - Limited to 50 results
    """
    try:
        results = autocomplete_dvp_team_by_gi_code(gi_code, q, pmt_code)
        return {"dvp_teams": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DVP team autocomplete failed: {str(e)}")

@router.get("/dvp-teams/autocomplete/by-gi-code", summary="Autocomplete DVP teams by GI code", description="Return DVP team suggestions for a specific GI code.")
def autocomplete_dvp_teams_by_gi_code(
    gi_code: str = Query(..., description="Vehicle-line GI code"),
    q: str = Query("", description="DVP team search term"),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Execute DVP team autocomplete search filtered by specific GI code.
    
    Args:
        gi_code: GI Code for filtering results (required)
        q: Search term for DVP team name (case-insensitive)
    
    Metrics:
        - dvp_teams: List of matching DVP teams for the specified GI code
        - count: Total count of results
        - message: User message if no results found
    
    Rules:
        - Returns ONLY DVP teams belonging to the specified gi_code
        - Case-insensitive LIKE matching
        - Limited to 50 results
        - Returns available count if search yields no results
    """
    try:
        results = autocomplete_dvp_team_by_gi_code(gi_code, q, pmt_code)
        if not results and q:
            # Fetch the unfiltered count to provide useful empty-result context.
            all_teams = autocomplete_dvp_team_by_gi_code(gi_code, "", pmt_code)
            return {
                "gi_code": gi_code,
                "dvp_teams": [],
                "count": 0,
                "message": f"No DVP team for GI code '{gi_code}' contains '{q}'. Available: {len(all_teams)}"
            }
        return {"gi_code": gi_code, "dvp_teams": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DVP team autocomplete failed: {str(e)}")

@router.get("/cpsc/list", summary="List CPSCs by GI code", description="Return all distinct CPSC codes for the supplied GI code.")
def list_cpsc_by_gi_code(
    gi_code: str = Query(..., description="Vehicle-line GI code"),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Retrieve all unique CPSC codes for a given GI Code.

    Args:
        gi_code: GI Code for filtering results (required)

    Returns:
        - cpsc_codes: List of unique CPSC values
        - count: Total count of results

    Rules:
        - Returns ONLY CPSC codes belonging to the specified gi_code
        - Excludes null and empty values
        - Returns unique values only, ordered ASC
    """
    try:
        results = get_cpsc_by_gi_code(gi_code, pmt_code)
        return {"gi_code": gi_code, "cpsc_codes": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve CPSC codes: {str(e)}")

@router.get("/cpsc/autocomplete", summary="Autocomplete CPSCs by GI code", description="Return CPSC suggestions filtered by GI code and search term.")
def autocomplete_cpsc(
    gi_code: str = Query(..., description="Vehicle-line GI code"),
    q: str = Query("", description="CPSC search term"),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Execute CPSC autocomplete search filtered by GI code.

    Args:
        gi_code: GI Code for filtering results (required)
        q: Search term for filtering CPSC codes (case-insensitive)

    Returns:
        - cpsc_codes: List of matching CPSC values
        - count: Total count of results
        - message: User message if no results found

    Rules:
        - Returns ONLY CPSC codes belonging to the specified gi_code
        - Case-insensitive LIKE matching
        - Returns unique values only
        - Limited to 50 results
    """
    try:
        results = autocomplete_cpsc_by_gi_code(gi_code, q, pmt_code)
        if not results and q:
            all_cpsc = get_cpsc_by_gi_code(gi_code, pmt_code)
            return {
                "gi_code": gi_code,
                "cpsc_codes": [],
                "count": 0,
                "message": f"No CPSC for GI code '{gi_code}' contains '{q}'. Available: {len(all_cpsc)}"
            }
        return {"gi_code": gi_code, "cpsc_codes": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CPSC autocomplete failed: {str(e)}")

@router.get("/metrics/dvp-team-list", summary="Métricas por DVP Team - Lista Completa", description="Retorna métricas de conf_state agrupadas por cada DVP Team do gi_code")
def get_metrics_by_dvp_team_list_endpoint(
    gi_code: str = Query(..., description="GI Code do vehicle_line"),
    snapshot_date: str = Query(None, description="Snapshot date opcional")
):
    """
    Retrieve aggregated conf_state metrics for each DVP Team within a GI Code.
    
    Args:
        gi_code: GI Code for filtering results (required)
    
    Metrics (per DVP Team):
        - dvp_team: DVP team name
        - total_assessments: Total records for this DVP team
        - conf_state_summary.Meet: Count of Pass/Meet states
        - conf_state_summary.Does Not Meet: Count of Does Not Meet states
        - conf_state_summary.Unassessed: Count of Unassessed states
        - conf_state_summary.Approved Deviation: Count of Approved Deviation states
        - conf_state_summary.Cannot Assess: Count of Cannot Assess states
        - conf_state_summary.Not Applicable: Count of Not Applicable states
        - meet_percentage: Percentage of Meet status
    
    Rules:
        - Groups ALL records by dvp_team name
        - Returns one entry per unique dvp_team
        - Ordered alphabetically by dvp_team
        - Excludes null dvp_team and null/empty conf_state
    """
    try:
        result = get_metrics_by_dvp_team_list(gi_code, snapshot_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DVP team metrics: {str(e)}")

@router.get("/metrics/total-assessments", summary="Total assessment metrics", description="Return the total assessment count.")
def get_total_assessments(gi_code: str = Query(None, description="Optional GI code filter")):
    """
    Count total non-null assessments in FEDE status.
    
    Args:
        gi_code: Optional GI Code for filtering results
    
    Metrics:
        - total_assessments: Count of non-null assessment_id records
    
    Rules:
        - Counts only non-null assessment_id values
        - Filters by gi_code if provided
        - Returns global count if gi_code is None
    """
    try:
        result = count_total_assessments(gi_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to count assessments: {str(e)}")

@router.get("/metrics/conf-state", summary="Métricas - Conf State", description="Retorna contagens agrupadas por estado de conformidade")
def get_conf_state_metrics(
    gi_code: str = Query(None, description="GI Code para filtrar (opcional)"),
    snapshot_date: str = Query(None, description="Snapshot date opcional")
):
    """
    Aggregate conformance state counts grouped by state type.
    
    Args:
        gi_code: Optional GI Code for filtering results
    
    Metrics:
        - Meet: Count of Pass/Meet conformance states
        - Cannot_Assess: Count of Cannot Assess states
        - Not_Applicable: Count of Not Applicable states
        - Unassessed: Count of Unassessed states
        - Does_Not_Meet: Count of Does Not Meet states
        - Approved_Deviation: Count of Approved Deviation states
    
    Rules:
        - Combines Pass and Meet into single Meet category
        - Filters by gi_code if provided
        - Ignores null conf_state values
        - Ignores Design review report and other non-relevant states
    """
    try:
        result = count_conf_state_results(gi_code, snapshot_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to count conformance states: {str(e)}")

@router.get("/metrics/assessment-dvp-status", summary="DVP assessment CPSC distribution", description="Return DVP assessment conformance states grouped by CPSC.")
def get_assessment_dvp_status(gi_code: str = Query(..., description="Vehicle-line GI code")):
    """
    Retrieve DVP team assessment distribution aggregated by CPSC code.
    
    Args:
        gi_code: GI Code for filtering assessments (required)
    
    Metrics:
        - total_unique_dvp_teams: Count of unique DVP teams per CPSC
        - total_assessments_for_cpsc: Total assessment records per CPSC
        - Meet: Conformance meet count
        - Unassessed: Unassessed count
        - Does_Not_Meet: Non-conformance count
        - Approved_Deviation: Approved deviation count
        - Cannot_Assess: Cannot assess count
        - Not_Applicable: Not applicable count
    
    Rules:
        - Groups by CPSC code extracted from DVP team names
        - Filters by specified gi_code
        - Excludes null conf_state values
        - Aggregates all records per CPSC for accurate metrics
    """
    try:
        result = get_assessment_dvp_status(gi_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DVP assessment status: {str(e)}")

@router.get("/metrics/design-rules-evidences", summary="Design Rule evidence metrics", description="Return Design Rule evidence metrics grouped by milestone and model year.")
def get_design_rules_evidences(gi_code: str = Query(..., description="Vehicle-line GI code")):
    """
    Retrieve Design Rules Evidences metrics grouped by milestone and model year.
    
    Args:
        gi_code: GI Code for filtering evidences (required)
    
    Metrics:
        - model_year: Extracted from program field
        - milestone_date: Project milestone date
        - fede_milestone_date: FEDE milestone date
        - gpds_milestone: GPDS milestone value
        - recommended_milestone: Recommended milestone date
        - milestone_overdue_flag: Overdue status
        - sme_review_milestone: SME review date
        - meet: Conformance meet count
        - does_not_meet: Non-conformance count
        - unassessed: Unassessed count
    
    Rules:
        - Filters by gi_code
        - Extracts model year from first 4 digits of program field
        - Groups by milestone and model year
        - Orders by gi_code and model year
    """
    try:
        result = get_design_rules_evidences_metrics(gi_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve Design Rule evidence metrics: {str(e)}")


@router.get("/metrics/dr-evidences-by-assessment", summary="DR evidence metrics by assessment", description="Return DR evidence metrics grouped by assessment and milestone, with an optional CPSC filter.")
def get_assessment_milestone(
    gi_code: str = Query(..., description="Vehicle-line GI code"),
    cpsc: str = Query(None, description="Optional CPSC filter"),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Retrieve conformance metrics grouped by assessment_id and milestone fields.

    Args:
        gi_code: GI Code for filtering records (required)
        cpsc: CPSC code for additional filtering (optional)

    Metrics:
        - assessment_id: Assessment identifier
        - cpsc: CPSC code
        - model_year: Extracted from program field (first 4 digits)
        - milestone_date: Project milestone date
        - milestone_fede: FEDE milestone
        - gpds_milestone: GPDS milestone
        - recommended_milestone: Recommended milestone
        - milestone_overdue: Overdue flag
        - sme_review_milestone: SME review milestone
        - meet: Count of meet/pass records
        - does_not_meet: Count of does not meet records
        - unassessed: Count of unassessed records
        - total: Total records per group

    Rules:
        - Filters by gi_code (required)
        - Optionally filters by cpsc column
        - Groups by assessment_id + all milestone fields
        - Orders by gi_code and model_year
    """
    try:
        result = get_dr_evidences_by_assessment(gi_code, cpsc, pmt_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assessment milestone metrics: {str(e)}")


@router.get("/metrics/cae-graph", summary="CAE chart metrics", description="Return CAE data grouped by CPSC and assessment ID.")
def get_cae_graph(gi_code: str = Query(..., description="Vehicle-line GI code")):
    """
    Retrieve CAE assessment data grouped by CPSC code and assessment_id.
    
    Args:
        gi_code: GI Code for filtering CAE records (required)
    
    Metrics:
        - total_unique_dvp_teams: Unique DVP teams per CPSC-Assessment combination
        - total_records_for_assessment: Total records per assessment
        - meet: Conformance meet count
        - unassessed: Unassessed count
        - approved_deviation: Approved deviation count
        - does_not_meet: Non-conformance count
        - cannot_assess: Cannot assess count
        - not_applicable: Not applicable count
    
    Rules:
        - Filters by gi_id matching gi_code
        - EXCLUDES records where prototype_type contains 'CAE'
        - Requires non-null and non-empty conf_state
        - Groups by CPSC code and assessment_id combination
    """
    try:
        result = get_cae_graph_data(gi_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve CAE chart data: {str(e)}")


@router.get("/metrics/design-rule-classification", summary="Design Rule Classification - Distribution by Model Year and Program", description="Returns distribution of Design Rule classifications grouped by model year and program name")
def get_design_rule_classification_endpoint(
    model_year: str = Query(..., description="Model year (e.g. 2027)"),
    program_name: str = Query(..., description="Program name (e.g. U725_Special_Mackinaw)"),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Retrieve Design Rule classification distribution by model year and program.

    Args:
        model_year: Model year used as the initial project filter (required)
        program_name: Program name used as the initial project filter (required)

    Metrics:
        - applicable: Count of applicable design rules
        - carryover: Count of carryover and previously validated rules combined
        - not_applicable: Count of not applicable rules
        - unclassified: Count of unclassified rules
        - total: Total rule count

    Notes:
        - Filters dr_design_rule via STARTS_WITH(dr_pk2, '{model_year}_{program_name}')
        - Combines Carryover and Previously Validated into single carryover category
        - Groups by model year and program name extracted from dr_pk2
    """
    try:
        result = get_design_rule_classification(model_year, program_name, pmt_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve Design Rule classification: {str(e)}")


@router.get("/metrics/cae-total-assessments", summary="CAE Total Assessments", description="Returns total CAE assessment counts grouped by program")
def get_cae_total(
    gi_code: str = Query(..., description="GI Code from vehicle_line"),
    program: str = Query(None, description="Program name filter (optional, legacy)"),
    cpsc: str = Query(None, description="CPSC code filter from dvp_team (optional)"),
    pmt_code: str = Query(None, description="Optional PMT code"),
):
    """
    Retrieve total CAE assessment counts grouped by program.
    Filter by cpsc (from dvp_team) or program name.
    """
    try:
        result = get_cae_total_assessments(gi_code, program, cpsc, pmt_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving CAE total assessments: {str(e)}")


@router.get("/metrics/cae-detailed", summary="CAE detailed records", description="Return row-level CAE records grouped by CPSC and assessment name.")
def get_cae_detailed(
    gi_code: str = Query(..., description="Vehicle-line GI code"),
    program: str = Query(None, description="Optional program name")
):
    """
    Retrieve detailed CAE records (one row per assessment) for a given GI Code.

    Args:
        gi_code: GI Code for filtering CAE records (required)
        program: Optional program name for further filtering

    Returns:
        - Program, GI_ID, CPSC_Code, Assessment_Name, Test_Method_ID, Status, Prototype_Type

    Rules:
        - INCLUDES ONLY records where prototype_type contains 'CAE'
        - Requires non-null and non-empty conformance_state
        - CPSC code is extracted from dvp_team field
        - Ordered by CPSC_Code and Assessment_Name
    """
    try:
        result = get_cae_detailed_data(gi_code, program)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving CAE detailed records: {str(e)}")


@router_v1.get("/hir-completion", summary="HIR completion metrics", description="Return Hardware in Review completion metrics with optional filters.")
def hir_completion(
    gi_code: str = Query(..., description="Vehicle-line GI code"),
    cpsc: str = Query(None, description="Optional commodity CPSC code"),
    pmt_code: str = Query(None, description="Optional PMT code"),
    milestone_date: str = Query(None, description="Optional milestone date"),
    dvp_team: str = Query(None, description="Optional DVP team"),
):
    """
    Retrieve HIR (Hardware in Review) completion metrics for a given GI Code.
    
    Args:
        gi_code: GI Code for filtering HIR records (required)
        cpsc: Optional CPSC code filter
        pmt_code: Optional PMT code filter
        milestone_date: Optional milestone date filter
        dvp_team: Optional DVP Team filter
    
    Metrics:
        - program_name: Program name extracted from pk4
        - gi_code: GI Code identifier
        - milestone_date: Milestone date
        - dvp_team: DVP team name
        - pmt_code: PMT code
        - cpsc: Commodity CPSC code
        - with_evidence: Count of items with evidence (has_evidence = 'Y')
        - without_evidence: Count of items without evidence (has_evidence = 'N')
        - total_items: Total item count
        - completion_percentage: Percentage of items with evidence
    
    Rules:
        - Joins fede_daily_drassesmentvw (DR assessments) with fede_daily_fedestatus
        - Filters by HIR source (source LIKE 'HIR%')
        - Pre-loads data for the specified gi_code
        - Supports optional filtering by cpsc, pmt_code, and milestone_date
        - Groups by program_name, gi_code, milestone_date, dvp_team, pmt_code, cpsc
        - Orders by completion_percentage descending
    """
    try:
        result = get_hir_completion_metrics(
            gi_code,
            cpsc,
            pmt_code,
            milestone_date,
            dvp_team,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving HIR completion metrics: {str(e)}")
