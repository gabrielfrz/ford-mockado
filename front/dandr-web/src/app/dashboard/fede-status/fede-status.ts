import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { FedeStatusService } from '../../services/fede-status.service';
import { ToastService } from '../../shared/toast.service';

type AnyObject = { [key: string]: any };

/** Normalized FEDE assessment record displayed by the status table. */
export interface FedeDataRow {
  pp_id: string;
  gi_id: string;
  assessment_id: string;
  assessment_creator: any;
  assessment_creator__msk: string;
  min_feat_desc: string;
  plan_cmplt_date: any;
  conf_state: string;
  reqst_proto_type: string;
  test_method_title: string;
  test_method_id: string;
  schdl_location: any;
  assessment_lst_mod_usr: any;
  assessment_lst_mod_usr__msk: string;
  user_def_field: any;
  has_attach: string;
  has_issue_dev: string;
  assessment_id_url: string;
  assessor: any;
  assessor__msk: string;
  sched_finish: string;
  status: string;
  milestone_overdue: number;
  milestone_date: string;
  pk4_rec: number;
  rec_milestone: string;
  right_prgm: any;
  actual_prototype_id: any;
  test_plan_request_no: any;
  test_status: string;
  assessment_explanation_dvpr_view: any;
  assessment_explanation_dvpr_view__msk: any;
  req_id: string;
  reporting: string;
  actual_end_date: any;
  gpds_milestone: string;
  lead_engineer: any;
  lead_engineer__msk: string;
  milestone_fede: string;
  no_dv_attempts: any;
  prototype_type: string;
  reqt_revision: string;
  sme_comments: any;
  sme_review: any;
  sme_review_history: any;
  sme_review_milestone: any;
  unique_c: string;
  unique_pgrm: string;
  feature: any;
  approval_date: any;
  assessed: string;
  critical: string;
  pk_rec: string;
  requirement_type: string;
  pmt_pat: string;
  pmt_code: string;
  vehicle_line: string;
  un_up: string;
  contacts: any;
  contacts__msk: string;
  pmt_leader: any;
  pmt_leader__msk: any;
  date_dt: string;
  cpsc: string;
  feature_domain: any;
  feature_family: any;
  feature_group: any;
  p_code: any;
  conway_prod: string;
  right_date: any;
  glidepath_start_date: any;
  glidepath_end_date: any;
  milestone_date2: any;
  exception_cat: any;
  test_time: string;
  test_time_unit: string;
  schdld_strt_dt: any;
  approval_sts: any;
  approver: any;
  approver__msk: any;
  t_rqst_no: any;
  t_assess_time: string;
  t_pln_strt: any;
  t_pln_fnsh: any;
  right_critical: string;
  pk1: string;
  pk2: string;
  pk3: string;
  pk4: string;
  pk1_rec: number;
  pk3_rec: number;
  right_pk4_rec: number;
  cae_flag: string;
  feature2: any;
  pk2_rec2: number;
  program: string;
  df_row_created_date: string;
  _dfgdia_iso3_country_std_cnty: any;
}

@Component({
  selector: 'app-fede-status',
  standalone: true,
  imports: [CommonModule, FormsModule, AutoCompleteModule, ButtonModule, TableModule],
  templateUrl: './fede-status.html',
  styleUrls: ['./fede-status.scss'],
})
/** Search and display FEDE assessment records by DVP team. */
export class FedeStatus implements OnChanges {
  @Input() set giCode(value: string | null) {
    console.log('[INPUT] giCode received:', value);
    this._giCode = value;
  }
  get giCode(): string | null {
    return this._giCode;
  }
  private _giCode: string | null = null;

  dvpTeamInput: string = '';
  dvpTeamSuggestions: string[] = [];
  selectedDvpTeam: string | null = null;
  dvpTeamLoading = false;
  dvpTeamError: string | null = null;
  fedeRows: FedeDataRow[] = [];
  fedeRowLoading = false;
  fedeRowError: string | null = null;

  constructor(private fedeService: FedeStatusService, private toastService: ToastService) {}

  ngOnChanges(changes: SimpleChanges): void {
    console.log('[CHANGES] ngOnChanges triggered:', changes);
    if (changes['giCode'] && changes['giCode'].currentValue) {
      console.log('[CHANGES] giCode changed to:', changes['giCode'].currentValue);
      this.loadDvpTeamsByGiCode(changes['giCode'].currentValue);
    } else {
      console.log('[CHANGES] giCode is empty or not changed');
    }
  }

  private loadDvpTeamsByGiCode(giCode: string): void {
    console.log('[LOAD] loadDvpTeamsByGiCode called with:', giCode);
    this.dvpTeamLoading = true;
    this.dvpTeamError = null;
    // An empty query preloads every DVP team in the selected program.
    this.fedeService.getDvpTeamsByGiCode(giCode, '').subscribe({
      next: (suggestions: string[]) => {
        console.log('[SUCCESS] DVP Teams loaded:', suggestions);
        this.dvpTeamSuggestions = suggestions;
        console.log('[SUCCESS] dvpTeamSuggestions updated:', this.dvpTeamSuggestions);
        this.toastService.success('Success!', `${suggestions.length} DVP team(s) preloaded for the GI code`);
      },
      error: (err: any) => {
        console.error('[ERROR] Error loading DVP Teams by GI Code:', err);
        this.dvpTeamError = 'Error loading DVP Teams';
        this.dvpTeamSuggestions = [];
        this.toastService.error('Error', 'Could not load DVP teams for this GI code');
      },
      complete: () => {
        console.log('[COMPLETE] loadDvpTeamsByGiCode completed');
        this.dvpTeamLoading = false;
      }
    });
  }

  // Restrict DVP team suggestions to the selected GI code.
  filterDvpTeams(event: any) {
    console.log('[FILTER] filterDvpTeams triggered, giCode:', this.giCode);

    if (!this.giCode) {
      console.log('[FILTER] No giCode available');
      this.toastService.warning('Warning', 'Select a vehicle line first');
      return;
    }

    const q = event.query || '';
    console.log('[FILTER] Searching with query:', q);
    this.dvpTeamLoading = true;
    this.dvpTeamError = null;
    this.fedeService.getDvpTeamsByGiCode(this.giCode, q).subscribe({
      next: (suggestions: string[]) => {
        console.log('[FILTER] Search results:', suggestions);
        this.dvpTeamSuggestions = suggestions;
        // Notify only after a non-empty user search.
        const queryTrimmed = (event.query || '').trim();
        if (queryTrimmed.length > 0 && suggestions.length > 0) {
          this.toastService.success('Success!', `${suggestions.length} DVP team(s) found`);
        }
      },
      error: (err: any) => {
        console.error('[FILTER] Error loading DVP Team suggestions:', err);
        this.dvpTeamError = 'Error loading suggestions';
        this.dvpTeamSuggestions = [];
        this.toastService.error('Error', 'Could not load DVP teams');
      },
      complete: () => {
        console.log('[FILTER] filterDvpTeams completed');
        this.dvpTeamLoading = false;
      }
    });
  }

  // DVP team selection
  onDvpTeamSelect(event: any) {
    const dvpTeam = typeof event === 'string' ? event : event?.value || event;

    if (!dvpTeam) {
      this.toastService.warning('Warning', 'Select a DVP team');
      return;
    }

    this.selectedDvpTeam = dvpTeam;
    this.fedeRows = [];
    this.fedeRowError = null;
    this.fedeRowLoading = true;
    this.toastService.info('Loading...', 'Fetching DVP team data');

    this.fedeService.getFedeStatusByDvpTeam(dvpTeam).subscribe({
      next: (data: any) => {
        // Normalize a single record and a record array to the same mapping path.
        if (Array.isArray(data)) {
          this.fedeRows = this.mapDataToRows(data);
        } else if (data && typeof data === 'object') {
          this.fedeRows = this.mapDataToRows([data]);
        } else {
          this.fedeRows = [];
        }
        this.toastService.success('Success!', `${this.fedeRows.length} record(s) loaded`);
      },
      error: (err: any) => {
        console.error('Error loading FEDE data:', err);
        this.fedeRowError = err?.error?.message || 'Error loading data';
        this.fedeRows = [];
        this.toastService.error('Error', 'Could not load DVP team data');
      },
      complete: () => {
        this.fedeRowLoading = false;
      }
    });
  }

  private mapDataToRows(data: any[]): FedeDataRow[] {
    return data.map(item => ({
      pp_id: item.pp_id || 'N/A',
      gi_id: item.gi_id || 'N/A',
      assessment_id: item.assessment_id || '',
      assessment_creator: item.assessment_creator || null,
      assessment_creator__msk: item.assessment_creator__msk || '',
      min_feat_desc: item.min_feat_desc || '',
      plan_cmplt_date: item.plan_cmplt_date || null,
      conf_state: item.conf_state || '',
      reqst_proto_type: item.reqst_proto_type || '',
      test_method_title: item.test_method_title || '',
      test_method_id: item.test_method_id || '',
      schdl_location: item.schdl_location || null,
      assessment_lst_mod_usr: item.assessment_lst_mod_usr || null,
      assessment_lst_mod_usr__msk: item.assessment_lst_mod_usr__msk || '',
      user_def_field: item.user_def_field || null,
      has_attach: item.has_attach || 'N',
      has_issue_dev: item.has_issue_dev || 'N',
      assessment_id_url: item.assessment_id_url || '',
      assessor: item.assessor || null,
      assessor__msk: item.assessor__msk || '',
      sched_finish: item.sched_finish || '',
      status: item.status || '',
      milestone_overdue: Number(item.milestone_overdue) || 0,
      milestone_date: item.milestone_date || '',
      pk4_rec: Number(item.pk4_rec) || 0,
      rec_milestone: item.rec_milestone || '',
      right_prgm: item.right_prgm || null,
      actual_prototype_id: item.actual_prototype_id || null,
      test_plan_request_no: item.test_plan_request_no || null,
      test_status: item.test_status || '',
      assessment_explanation_dvpr_view: item.assessment_explanation_dvpr_view || null,
      assessment_explanation_dvpr_view__msk: item.assessment_explanation_dvpr_view__msk || null,
      req_id: item.req_id || '',
      reporting: item.reporting || '',
      actual_end_date: item.actual_end_date || null,
      gpds_milestone: item.gpds_milestone || '',
      lead_engineer: item.lead_engineer || null,
      lead_engineer__msk: item.lead_engineer__msk || '',
      milestone_fede: item.milestone_fede || '',
      no_dv_attempts: item.no_dv_attempts || null,
      prototype_type: item.prototype_type || '',
      reqt_revision: item.reqt_revision || '',
      sme_comments: item.sme_comments || null,
      sme_review: item.sme_review || null,
      sme_review_history: item.sme_review_history || null,
      sme_review_milestone: item.sme_review_milestone || null,
      unique_c: item.unique_c || 'N',
      unique_pgrm: item.unique_pgrm || '',
      feature: item.feature || null,
      approval_date: item.approval_date || null,
      assessed: item.assessed || '0.0',
      critical: item.critical || '',
      pk_rec: item.pk_rec || '',
      requirement_type: item.requirement_type || '',
      pmt_pat: item.pmt_pat || '',
      pmt_code: item.pmt_code || '',
      vehicle_line: item.vehicle_line || '',
      un_up: item.un_up || '',
      contacts: item.contacts || null,
      contacts__msk: item.contacts__msk || '',
      pmt_leader: item.pmt_leader || null,
      pmt_leader__msk: item.pmt_leader__msk || null,
      date_dt: item.date_dt || '',
      cpsc: item.cpsc || '',
      feature_domain: item.feature_domain || null,
      feature_family: item.feature_family || null,
      feature_group: item.feature_group || null,
      p_code: item.p_code || null,
      conway_prod: item.conway_prod || '',
      right_date: item.right_date || null,
      glidepath_start_date: item.glidepath_start_date || null,
      glidepath_end_date: item.glidepath_end_date || null,
      milestone_date2: item.milestone_date2 || null,
      exception_cat: item.exception_cat || null,
      test_time: item.test_time || '0',
      test_time_unit: item.test_time_unit || '',
      schdld_strt_dt: item.schdld_strt_dt || null,
      approval_sts: item.approval_sts || null,
      approver: item.approver || null,
      approver__msk: item.approver__msk || null,
      t_rqst_no: item.t_rqst_no || null,
      t_assess_time: item.t_assess_time || '',
      t_pln_strt: item.t_pln_strt || null,
      t_pln_fnsh: item.t_pln_fnsh || null,
      right_critical: item.right_critical || '',
      pk1: item.pk1 || '',
      pk2: item.pk2 || '',
      pk3: item.pk3 || '',
      pk4: item.pk4 || '',
      pk1_rec: Number(item.pk1_rec) || 0,
      pk3_rec: Number(item.pk3_rec) || 0,
      right_pk4_rec: Number(item.right_pk4_rec) || 0,
      cae_flag: item.cae_flag || '',
      feature2: item.feature2 || null,
      pk2_rec2: Number(item.pk2_rec2) || 0,
      program: item.program || '',
      df_row_created_date: item.df_row_created_date || '',
      _dfgdia_iso3_country_std_cnty: item._dfgdia_iso3_country_std_cnty || null
    }));
  }

  getConfStateColor(state: string): string {
    if (state.toLowerCase().includes('meet')) {
      return 'green';
    } else if (state.toLowerCase().includes('does not meet')) {
      return 'red';
    }
    return 'inherit';
  }

  isOverdue(overdue: number): boolean {
    return overdue > 0;
  }

  getTableColumns(): string[] {
    if (this.fedeRows.length === 0) return [];
    return Object.keys(this.fedeRows[0]);
  }

  getCellValue(row: any, key: string): string {
    const value = row[key];
    if (value === null || value === undefined) return '';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  }

  getCellColor(key: string, value: string): string {
    if (key === 'conf_state' && value.toLowerCase().includes('meet')) return 'green';
    if (key === 'conf_state' && value.toLowerCase().includes('does not meet')) return 'red';
    if (key === 'milestone_overdue' && Number(value) > 0) return 'red';
    return 'inherit';
  }
}

