import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../core/api-config';

/** DPA5 compliance targets at one glidepath milestone. */
export interface Dpa5GlidepathPoint {
  milestone_date: string;
  milestone_name: string | null;
  compliant: number;
  not_compliant: number;
  not_assessable: number;
  assessment_goal_curve: number | null;
  compliance_goal_curve: number | null;
  compliance_prediction: number | null;
}

/** Aggregate DPA5 compliance counts. */
export interface Dpa5Summary {
  compliant: number;
  not_compliant: number;
  not_assessable: number;
  total: number;
}

/** DPA5 summary and glidepath response. */
export interface Dpa5SummaryResponse {
  gi_code: string;
  cpsc_filter: string | null;
  summary: Dpa5Summary;
  glidepath: Dpa5GlidepathPoint[];
  error?: string;
}

@Injectable({ providedIn: 'root' })
/** Access DPA5 summaries, glidepaths, and selector values. */
export class Dpa5Service {
  private readonly baseUrl = `${API_BASE_URL}/dpa5`;

  constructor(private http: HttpClient) {}

  /** Retrieve DPA5 summary totals and glidepath values. */
  getSummary(giCode: string, cpsc?: string, pmt?: string, snapshotDate?: string): Observable<Dpa5SummaryResponse> {
    let params = new HttpParams().set('gi_code', giCode);
    if (cpsc) params = params.set('cpsc', cpsc);
    if (pmt)  params = params.set('pmt', pmt);
    if (snapshotDate) params = params.set('snapshot_date', snapshotDate);
    return this.http.get<Dpa5SummaryResponse>(`${this.baseUrl}/summary`, { params });
  }

  /** Retrieve available DPA5 snapshot labels. */
  getSnapshots(giCode: string): Observable<{ gi_code: string; snapshots: string[] }> {
    const params = new HttpParams().set('gi_code', giCode);
    return this.http.get<{ gi_code: string; snapshots: string[] }>(`${this.baseUrl}/snapshots`, { params });
  }

  /** Retrieve CPSC values available for a GI code and optional PMT. */
  getCpscList(giCode: string, pmt?: string): Observable<{ gi_code: string; pmt_filter: string | null; cpsc_codes: string[]; count: number }> {
    let params = new HttpParams().set('gi_code', giCode);
    if (pmt) params = params.set('pmt', pmt);
    return this.http.get<any>(`${this.baseUrl}/cpsc-list`, { params });
  }
}
