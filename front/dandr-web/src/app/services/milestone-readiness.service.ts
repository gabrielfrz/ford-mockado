import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../core/api-config';

/** Readiness target, actual value, percentage, and status for one source. */
export interface MilestoneMetric {
  source: string;
  target: number;
  actual: number;
  percentage: number;
  status: 'green' | 'yellow' | 'red';
}

/** Cross-deliverable readiness response for one milestone. */
export interface MilestoneReadinessResponse {
  milestone: string;
  program: string;
  milestone_date: string;
  pmt_code?: string | null;
  metrics: MilestoneMetric[];
}

@Injectable({ providedIn: 'root' })
/** Retrieve milestone-readiness metrics from the backend. */
export class MilestoneReadinessService {
  private readonly baseUrl = API_BASE_URL;

  constructor(private http: HttpClient) {}

  /** Retrieve cross-deliverable readiness for one vehicle milestone. */
  getReadiness(giCode: string, milestone: string, pmtCode?: string | null): Observable<MilestoneReadinessResponse> {
    let params = new HttpParams().set('milestone', milestone.toLowerCase());
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http.get<MilestoneReadinessResponse>(
      `${this.baseUrl}/api/v1/milestone-readiness/${encodeURIComponent(giCode)}`,
      { params }
    );
  }
}
