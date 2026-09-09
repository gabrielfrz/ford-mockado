import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { API_BASE_URL } from '../core/api-config';

/** DVP requirement-classification totals. */
export interface DvpClassificationResponse {
  program: string;
  total: number;
  classified: number;
  not_classified: number;
  percentage: number;
}

/** HIR completion metrics for one filter group. */
export interface HirCompletionData {
  program_name: string;
  gi_code: string;
  milestone_date: string | null;
  dvp_team: string | null;
  pmt_code: string | null;
  cpsc: string;
  with_evidence: number;
  without_evidence: number;
  total_items: number;
  completion_percentage: number;
}

/** HIR completion response and applied filters. */
export interface HirCompletionResponse {
  gi_code: string;
  cpsc: string | null;
  pmt_code: string | null;
  milestone_date: string | null;
  data: HirCompletionData[];
  total_records: number;
}

@Injectable({ providedIn: 'root' })
/** Access FEDE status, DVP, CAE, Design Rule, and HIR endpoints. */
export class FedeStatusService {
  private readonly rootUrl    = API_BASE_URL;
  private readonly standardUrl = `${this.rootUrl}/fede-status`;
  private readonly apiV1Url    = `${this.rootUrl}/api/v1/fede-status`;

  constructor(private http: HttpClient) {}

  /** Retrieve DVP teams restricted to a GI code and optional filters. */
  getDvpTeamsByGiCode(giCode: string, query?: string, pmtCode?: string | null): Observable<string[]> {
    let params = new HttpParams().set('gi_code', giCode);
    if (query) {
      params = params.set('q', query);
    }
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http
      .get<{ dvp_teams: string[] }>(`${this.standardUrl}/dvp-teams/autocomplete/by-gi-code`, { params })
      .pipe(map(res => res.dvp_teams || []));
  }

  /** Retrieve the detailed FEDE assessment row for a DVP team. */
  getFedeStatusByDvpTeam(dvpTeam: string): Observable<any> {
    const params = new HttpParams().set('dvp_team', dvpTeam);
    return this.http
      .get<{ result: any }>(`${this.standardUrl}/by-dvp-team/row`, { params })
      .pipe(map(res => res.result || null));
  }

  /** Retrieve aggregate conformance-state counts for a DVP team. */
  getConfStateMetricsByDvpTeam(dvpTeam: string, snapshotDate?: string | null): Observable<any> {
    let params = new HttpParams().set('dvp_team', dvpTeam);
    if (snapshotDate && snapshotDate !== 'null') params = params.set('snapshot_date', snapshotDate);
    return this.http
      .get<any>(`${this.standardUrl}/metrics/conf-state-by-dvp-team`, { params })
      .pipe(map(res => res));
  }

  /** Retrieve conformance metrics for every DVP team in a GI code. */
  getDvpTeamListMetrics(giCode: string, snapshotDate?: string | null, pmtCode?: string | null): Observable<any> {
    let params = new HttpParams().set('gi_code', giCode);
    if (snapshotDate && snapshotDate !== 'null') params = params.set('snapshot_date', snapshotDate);
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http
      .get<any>(`${this.standardUrl}/metrics/dvp-team-list`, { params })
      .pipe(map(res => res));
  }

  /** Retrieve aggregate conformance-state metrics for a GI code. */
  getConfStateMetrics(giCode: string, snapshotDate?: string | null, pmtCode?: string | null): Observable<any> {
    let params = new HttpParams().set('gi_code', giCode);
    if (snapshotDate && snapshotDate !== 'null') params = params.set('snapshot_date', snapshotDate);
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http
      .get<any>(`${this.standardUrl}/metrics/conf-state`, { params })
      .pipe(map(res => res));
  }

  /** Retrieve conformance-state metrics grouped by CPSC. */
  getCpscConfStateBreakdown(giCode: string): Observable<any> {
    const params = new HttpParams().set('gi_code', giCode);
    return this.http
      .get<any>(`${this.standardUrl}/metrics/cpsc-conf-state-breakdown`, { params })
      .pipe(map(res => res));
  }

  /** Retrieve DVP classification totals for a GI code and CPSC. */
  getDvpClassification(
    giCode: string,
    cpsc: string,
    snapshotDate?: string | null,
    pmtCode?: string | null
  ): Observable<DvpClassificationResponse> {
    let params = new HttpParams().set('gi_code', giCode).set('cpsc', cpsc);
    if (snapshotDate && snapshotDate !== 'null') params = params.set('snapshot_date', snapshotDate);
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http
      .get<DvpClassificationResponse>(`${this.apiV1Url}/dvp-classification`, { params })
      .pipe(map(res => res));
  }

  /** Retrieve HIR evidence completion metrics for the supplied filters. */
  getHirCompletion(
    giCode: string,
    cpsc?: string | null,
    pmtCode?: string | null,
    milestoneDate?: string | null,
    dvpTeam?: string | null
  ): Observable<HirCompletionResponse> {
    let params = new HttpParams().set('gi_code', giCode);
    if (cpsc) params = params.set('cpsc', cpsc);
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    if (milestoneDate) params = params.set('milestone_date', milestoneDate);
    if (dvpTeam) params = params.set('dvp_team', dvpTeam);
    return this.http
      .get<HirCompletionResponse>(`${this.apiV1Url}/hir-completion`, { params })
      .pipe(map(res => res));
  }
}
