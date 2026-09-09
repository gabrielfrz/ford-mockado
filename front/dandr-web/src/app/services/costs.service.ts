import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { API_BASE_URL } from '../core/api-config';

/** CPSC values returned for an Effective Point. */
export interface CpscListResponse {
  effectivein: string;
  cpsc_codes: string[];
  count: number;
}

/** Source PMT values returned for an Effective Point. */
export interface PmtListResponse {
  effectivein: string;
  cpsc: string | null;
  pmt_codes: string[];
  count: number;
}

/** Canonical PMT values and source-specific mappings. */
export interface PmtGeneralResponse {
  pmt_codes: string[];
  mapping: Record<string, Record<string, string>>;
  count: number;
}

/** One normalized tooling- or piece-cost record. */
export interface CostDataItem {
  program: string;
  effectivein: string;
  pmt: string;
  partnumber: string;
  cpsc: string;
  cpsc_name: string;
  actual_tooling_cost?: number;
  target_tooling_cost?: number;
  actual_piece_cost?: number;
  target_piece_cost?: number;
  gap?: number;
  currency: string;
  source_reference: string;
}

/** Aggregate tooling-cost response from the API. */
export interface ToolingMetricsResponse {
  effectivein: string;
  cpsc: string | null;
  pmt_code: string | null;
  cost_type: 'tooling';
  total_records: number;
  total_cost: number;
  data: CostDataItem[];
}

/** Aggregate piece-cost response from the API. */
export interface PieceMetricsResponse {
  effectivein: string;
  cpsc: string | null;
  pmt_code: string | null;
  cost_type: 'piece';
  total_records: number;
  total_cost: number;
  data: CostDataItem[];
}

/** Part-number selector response. */
export interface PartNumberListResponse {
  q: string;
  part_numbers: string[];
  count: number;
}

/** Commodity selector item containing a CPSC and display name. */
export interface CommodityItem {
  cpsc: string;
  name: string;
}

/** Commodity selector response. */
export interface CommodityListResponse {
  commodities: CommodityItem[];
  count: number;
}

/** Vehicle-line selector response. */
export interface VehicleLineListResponse {
  vehicle_lines: string[];
  count: number;
}

/** Combined tooling- and piece-cost response. */
export interface CombinedMetricsResponse {
  effectivein: string;
  cpsc: string | null;
  pmt_code: string | null;
  tooling_cost: {
    cost_type: 'tooling';
    total_records: number;
    total_cost: number;
    data: CostDataItem[];
  };
  piece_cost: {
    cost_type: 'piece';
    total_records: number;
    total_cost: number;
    data: CostDataItem[];
  };
  summary: {
    total_tooling_cost: number;
    total_piece_cost: number;
    grand_total_cost: number;
    total_tooling_records: number;
    total_piece_records: number;
  };
}

@Injectable({ providedIn: 'root' })
/** Access cost filters, records, and aggregate metrics from the backend. */
export class CostsService {
  private readonly baseUrl = `${API_BASE_URL}/cost`;
  private readonly pmtBaseUrl = `${API_BASE_URL}/pmt`;

  constructor(private http: HttpClient) {}

  /**
   * Get general PMT list (100, 200, 300, 400, 500, 600) — independent of effectivein or CPSC
   */
  getPmtGeneralList(): Observable<PmtGeneralResponse> {
    return this.http.get<PmtGeneralResponse>(`${this.pmtBaseUrl}/list`);
  }

  /**
   * Get list of available CPSCs for a given effective point
   */
  getCpscList(effectivein: string): Observable<CpscListResponse> {
    const params = new HttpParams().set('effectivein', effectivein);
    return this.http.get<CpscListResponse>(`${this.baseUrl}/cpsc/list`, { params });
  }

  /**
   * Autocomplete search for CPSCs
   */
  autocompleteCpsc(effectivein: string, query?: string): Observable<CpscListResponse> {
    let params = new HttpParams().set('effectivein', effectivein);
    if (query) {
      params = params.set('q', query);
    }
    return this.http.get<CpscListResponse>(`${this.baseUrl}/cpsc/autocomplete`, { params });
  }

  /**
   * Get list of available PMTs for a given effective point and optional CPSC
   */
  getPmtList(effectivein: string, cpsc?: string): Observable<PmtListResponse> {
    let params = new HttpParams().set('effectivein', effectivein);
    if (cpsc) {
      params = params.set('cpsc', cpsc);
    }
    return this.http.get<PmtListResponse>(`${this.baseUrl}/pmt/list`, { params });
  }

  /**
   * Get tooling cost metrics
   */
  getToolingMetrics(effectivein: string, cpsc?: string, pmtCode?: string): Observable<ToolingMetricsResponse> {
    let params = new HttpParams().set('effectivein', effectivein);
    if (cpsc) {
      params = params.set('cpsc', cpsc);
    }
    if (pmtCode) {
      params = params.set('pmt_code', pmtCode);
    }
    return this.http.get<ToolingMetricsResponse>(`${this.baseUrl}/metrics/tooling`, { params });
  }

  /**
   * Get piece cost metrics
   */
  getPieceMetrics(effectivein: string, cpsc?: string, pmtCode?: string): Observable<PieceMetricsResponse> {
    let params = new HttpParams().set('effectivein', effectivein);
    if (cpsc) {
      params = params.set('cpsc', cpsc);
    }
    if (pmtCode) {
      params = params.set('pmt_code', pmtCode);
    }
    return this.http.get<PieceMetricsResponse>(`${this.baseUrl}/metrics/piece`, { params });
  }

  /**
   * Get list of available Part Numbers for a given effective point
   */
  getPartNumberList(effectivein: string, q?: string): Observable<PartNumberListResponse> {
    let params = new HttpParams().set('effectivein', effectivein);
    if (q) {
      params = params.set('q', q);
    }
    return this.http.get<PartNumberListResponse>(`${this.baseUrl}/partnumber/list`, { params });
  }

  /**
   * Get list of available Commodities (CPSC)
   */
  getCommodityList(effectivein: string): Observable<CommodityListResponse> {
    const params = new HttpParams().set('effectivein', effectivein);
    return this.http.get<CommodityListResponse>(`${this.baseUrl}/commodity/list`, { params });
  }

  /**
   * Get list of available Vehicle Lines (Control Model)
   */
  getVehicleLineList(effectivein: string): Observable<VehicleLineListResponse> {
    const params = new HttpParams().set('effectivein', effectivein);
    return this.http.get<VehicleLineListResponse>(`${this.baseUrl}/vehicleline/list`, { params });
  }

  /**
   * Get all dropdown data (partnumbers, commodities, vehicle lines) in a single BigQuery call.
   * Replaces the 3 separate calls to /partnumber/list, /commodity/list, /vehicleline/list.
   */
  getDropdownData(effectivein: string): Observable<{ effectivein: string; partnumbers: string[]; commodities: CommodityItem[]; vehicle_lines: string[] }> {
    const params = new HttpParams().set('effectivein', effectivein);
    return this.http.get<{ effectivein: string; partnumbers: string[]; commodities: CommodityItem[]; vehicle_lines: string[] }>(
      `${this.baseUrl}/dropdowns`, { params }
    );
  }

  /**
   * Get combined metrics (tooling + piece)
   */
  getCombinedMetrics(effectivein: string, cpsc?: string, pmtCode?: string): Observable<CombinedMetricsResponse> {
    let params = new HttpParams().set('effectivein', effectivein);
    if (cpsc) {
      params = params.set('cpsc', cpsc);
    }
    if (pmtCode) {
      params = params.set('pmt_code', pmtCode);
    }
    return this.http.get<CombinedMetricsResponse>(`${this.baseUrl}/metrics/combined`, { params });
  }
}
