import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { API_BASE_URL } from '../core/api-config';

@Injectable({ providedIn: 'root' })
/** Access vehicle-line metadata, selectors, and deliverable metrics. */
export class VehicleLineService {
  private readonly apiUrl = API_BASE_URL;

  constructor(private http: HttpClient) {}

  /** Retrieve model-year autocomplete values. */
  getModelYears(query: string): Observable<string[]> {
    const params = new HttpParams().set('query', query);
    return this.http
      .get<{ model_years?: string[] } | string[]>(`${this.apiUrl}/search/model-years`, { params })
      .pipe(map(res => Array.isArray(res) ? res : (res.model_years || [])));
  }

  /** Retrieve program-name autocomplete values for an optional model year. */
  getProgramNames(query: string, modelYear?: string): Observable<string[]> {
    let params = new HttpParams().set('query', query);
    if (modelYear) {
      params = params.set('model_year', modelYear);
    }
    return this.http
      .get<{ program_names?: string[] } | string[]>(`${this.apiUrl}/search/program-names`, { params })
      .pipe(map(res => Array.isArray(res) ? res : (res.program_names || [])));
  }

  /** Retrieve project-description autocomplete values for optional filters. */
  getProgramCodes(query: string, modelYear?: string, programName?: string): Observable<string[]> {
    let params = new HttpParams().set('query', query);
    if (modelYear) {
      params = params.set('model_year', modelYear);
    }
    if (programName) {
      params = params.set('program_name', programName);
    }
    return this.http
      .get<{ program_codes?: string[] } | string[]>(`${this.apiUrl}/search/program-codes`, { params })
      .pipe(map(res => Array.isArray(res) ? res : (res.program_codes || [])));
  }

  /** Retrieve the vehicle-line summary for the selected program. */
  getSummary(modelYear: string, programCodes: string, programNames?: string): Observable<any> {
    let params = new HttpParams()
      .set('model_year', modelYear)
      .set('program_codes', programCodes);

    if (programNames) {
      params = params.set('program_names', programNames);
    }

    return this.http
      .get<any>(`${this.apiUrl}/vehicle-line/`, { params });
  }

  /** Retrieve CAE chart data for a GI code. */
  getCaeGraphData(giCode: string): Observable<any> {
    const params = new HttpParams().set('gi_code', giCode);
    return this.http
      .get<any>(`${this.apiUrl}/metrics/cae-graph`, { params });
  }

  /** Retrieve CAE assessment totals for the supplied filters. */
  getCaeTotalAssessments(giCode: string, cpsc?: string, pmtCode?: string | null): Observable<any> {
    let params = new HttpParams().set('gi_code', giCode);
    if (cpsc) {
      params = params.set('cpsc', cpsc);
    }
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http
      .get<any>(`${this.apiUrl}/fede-status/metrics/cae-total-assessments`, { params });
  }

  /** Retrieve CPSC values used by the CAE and HIR selectors. */
  getCommoditiesByGiCode(giCode: string, pmtCode?: string | null): Observable<string[]> {
    let params = new HttpParams().set('gi_code', giCode);
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http
      .get<{ cpsc_codes: string[] }>(`${this.apiUrl}/fede-status/cpsc/list`, { params })
      .pipe(map(res => res.cpsc_codes || []));
  }

  /** Retrieve CPSC values used by the Design Rule selector. */
  getCpscListByGiCode(giCode: string, pmtCode?: string | null): Observable<string[]> {
    let params = new HttpParams().set('gi_code', giCode);
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http
      .get<{ cpsc_codes: string[] }>(`${this.apiUrl}/fede-status/cpsc/list`, { params })
      .pipe(map(res => res.cpsc_codes || []));
  }

  /** Retrieve Design Rule classifications by model year and program. */
  getDrClassification(modelYear: string, programName: string, pmtCode?: string | null): Observable<any> {
    let params = new HttpParams()
      .set('model_year', modelYear)
      .set('program_name', programName);
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http
      .get<any>(`${this.apiUrl}/fede-status/metrics/design-rule-classification`, { params });
  }

  /** Retrieve Design Rule evidence metrics grouped by assessment. */
  getDrEvidencesByAssessment(giCode: string, cpsc?: string | null, pmtCode?: string | null): Observable<any> {
    let params = new HttpParams().set('gi_code', giCode);
    if (cpsc) {
      params = params.set('cpsc', cpsc);
    }
    if (pmtCode) params = params.set('pmt_code', pmtCode);
    return this.http
      .get<any>(`${this.apiUrl}/fede-status/metrics/dr-evidences-by-assessment`, { params });
  }
}
