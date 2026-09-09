import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_BASE_URL } from '../core/api-config';

/** Conformance counts associated with a DVP glidepath record. */
export interface DvpGlidepathMetrics {
  meet: number;
  does_not_meet: number;
  unassessed: number;
  total: number;
}

/** One dated DVP glidepath data point. */
export interface DvpGlidepathRecord {
  gi_code: string;
  pmt_code: string;
  model_year: string;
  milestone: string | null;
  scheduled_finished: string | null;
  actual_finished: string | null;
  metrics: DvpGlidepathMetrics;
}

interface DvpGlidepathResponse {
  data: DvpGlidepathRecord[];
}

@Injectable({ providedIn: 'root' })
/** Access DVP glidepath data and available filters. */
export class DvpGlidepathService {
  private readonly baseUrl = `${API_BASE_URL}/api/v1/dvp-glidepath`;

  constructor(private http: HttpClient) {}

  /** Retrieve PMT values available for a DVP glidepath. */
  getPmts(giCode: string): Observable<string[]> {
    const params = new HttpParams().set('gi_code', giCode);
    return this.http.get<string[]>(`${this.baseUrl}/pmts`, { params });
  }

  /** Retrieve milestone dates available for a GI code and PMT. */
  getMilestones(giCode: string, pmt: string): Observable<string[]> {
    const params = new HttpParams().set('gi_code', giCode).set('pmt', pmt);
    return this.http.get<string[]>(`${this.baseUrl}/milestones`, { params });
  }

  /** Retrieve DVP glidepath records for the supplied filters. */
  getData(giCode: string, pmt?: string | null, milestone?: string | null, snapshotDate?: string | null): Observable<DvpGlidepathRecord[]> {
    let params = new HttpParams().set('gi_code', giCode);
    if (pmt) params = params.set('pmt', pmt);
    if (milestone) params = params.set('milestone', milestone);
    if (snapshotDate) params = params.set('snapshot_date', snapshotDate);
    return this.http.get<DvpGlidepathResponse>(`${this.baseUrl}/data`, { params })
      .pipe(map(res => res.data ?? []));
  }

  /** Retrieve snapshot dates exposed by the DVP data endpoint. */
  getSnapshots(giCode: string): Observable<{ gi_code: string; snapshots: string[] }> {
    const params = new HttpParams().set('gi_code', giCode);
    return this.http.get<{ gi_code: string; snapshots: string[] }>(`${this.baseUrl}/snapshots`, { params });
  }
}
