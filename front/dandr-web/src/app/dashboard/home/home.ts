import { Component, HostBinding } from '@angular/core';
import { VehicleLineService } from '../../services/vehicle-line.service';
import { FedeStatusService } from '../../services/fede-status.service';
import { CostsService } from '../../services/costs.service';
import { Dpa5Service } from '../../services/dpa5.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { ButtonModule } from 'primeng/button';
import { StateService, ChartType } from '../../shared/state.service';
import { ToastService } from '../../shared/toast.service';
import { TimelineMilestones } from '../components/timeline-milestones/timeline-milestones';
import { DesignRulesChart } from '../components/design-rules-chart/design-rules-chart';
import { CaeStatusComponent } from '../components/cae-status/cae-status';
import { CaeMetricsComponent } from '../components/cae-metrics/cae-metrics';
import { HirMetricsComponent } from '../components/hir-metrics/hir-metrics';
import { DvpTotalComponent } from '../components/dvp-total/dvp-total';
import { DvpClassificationComponent } from '../components/dvp-classification/dvp-classification';
import { ExtractButtonComponent } from '../components/extract-button';
import { CostsStatusComponent } from '../costs-status/costs-status';
import { Dpa5MetricsComponent } from '../components/dpa5-metrics/dpa5-metrics';
import { DvpGlidepathComponent } from '../components/dvp-glidepath/dvp-glidepath';
import { API_BASE_URL } from '../../core/api-config';
import { DvpGlidepathService } from '../../services/dvp-glidepath.service';

interface Option {
  label: string;
  value: string;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule, AutoCompleteModule, ButtonModule, TimelineMilestones, DesignRulesChart, CaeMetricsComponent, HirMetricsComponent, DvpTotalComponent, DvpClassificationComponent, ExtractButtonComponent, CostsStatusComponent, Dpa5MetricsComponent, DvpGlidepathComponent],
  templateUrl: './home.html',
  styleUrls: ['./home.scss'],
})
/** Coordinate vehicle selection, deliverable filters, and dashboard content. */
export class Home {
  modelYear!: Option | null;
  programName!: Option | null;
  programCode!: Option | null;

  filteredModelYears: Option[] = [];
  filteredProgramNames: Option[] = [];
  filteredProgramCodes: Option[] = [];

  submitted = false;
  summaryData: any = null;
  hasValidSummary = false;
  isLoadingData = false;
  activeChart: ChartType = null;
  showKeyEngineering = false;
  selectedDvpTeam: string | null = null;
  selectedDvpCpsc: string | null = null;
  dvpView: 'assessment' | 'classification' = 'assessment';
  costsView: 'pieces' | 'tooling' = 'pieces';
  drView: 'evidences' | 'classification' = 'evidences';
  selectedDrCommodity: string | null = null;
  availableDrCpscCodes: string[] = [];
  selectedProgram: string | null = null;
  availablePrograms: string[] = [];
  availableDvpTeams: string[] = [];
  selectedHirDvpTeam: string | null = null;
  availableHirDvpTeams: string[] = [];
  selectedCostsCpsc: string | null = null;
  selectedCostsPmt: string | null = null;
  availableCostsCpscs: string[] = [];
  availableCostsPmts: string[] = [];
  selectedDpa5Pmt: string | null = null;
  availableDpa5Cpscs: string[] = [];
  selectedDpa5Cpsc: string | null = null;
  isLoadingDpa5Cpscs = false;
  selectedDpa5SnapshotDate: string | null = null;
  availableDpa5SnapshotDates: string[] = [];
  selectedDvpPmt: string | null = null;
  selectedDvpMilestone: string | null = null;
  availableDvpMilestones: string[] = [];
  dvpGlidepathPmtList: string[] = [];
  dvpGlidepathMilestoneList: string[] = [];
  selectedDvpSnapshotDate: string | null = null;
  availableDvpSnapshotDates: string[] = [];

  private readonly chartExportConfig: Record<Exclude<ChartType, null>, { endpointUrl: string; filePrefix: string; enabled: boolean }> = {
    cae: {
      endpointUrl: `${API_BASE_URL}/export/cae-status`,
      filePrefix: 'CAE_Report',
      enabled: true
    },
    dvp: {
      endpointUrl: `${API_BASE_URL}/export/dvp-team-assessment`,
      filePrefix: 'dvp-team-assessment-report',
      enabled: true
    },
    hir: {
      endpointUrl: `${API_BASE_URL}/export/hir`,
      filePrefix: 'HIR_Report',
      enabled: true
    },
     designRules: {
      endpointUrl: `${API_BASE_URL}/export/design-rule`,
      filePrefix: 'design_rule',
      enabled: true
    },
    costs: {
      endpointUrl: `${API_BASE_URL}/export/costs`,
      filePrefix: 'Costs_Report',
      enabled: true
    },
    dpa5: {
      endpointUrl: `${API_BASE_URL}/export/dpa5`,
      filePrefix: 'DPA5_Report',
      enabled: true
    }
  };

  @HostBinding('class.processed')
  get hostProcessed() { return this.hasValidSummary; }

  get currentExtractEndpointUrl(): string {
    if (!this.activeChart) return '';
    return this.chartExportConfig[this.activeChart].endpointUrl;
  }

  get currentExtractFileName(): string {
    if (this.activeChart === 'dvp') {
      if (this.selectedDvpTeam && this.selectedDvpTeam !== 'null') {
        const teamSlug = this.selectedDvpTeam.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 40);
        return `dvp-team-assessment-${teamSlug}.xlsx`;
      }
      return 'dvp-team-assessment-report.xlsx';
    }
    const suffix = this.summaryData?.gi_code || this.summaryData?.program_code || 'export';
    if (!this.activeChart) return `Report_${suffix}.xlsx`;
    return `${this.chartExportConfig[this.activeChart].filePrefix}_${suffix}.xlsx`;
  }

  get currentExtractParams(): Record<string, any> {
    const params: Record<string, any> = {};
    if (!this.activeChart) return params;

    switch (this.activeChart) {
      case 'cae':
        params['gi_id'] = this.summaryData?.gi_code;
        if (this.selectedCostsPmt && this.selectedCostsPmt !== 'null') {
          params['pmt_code'] = this.selectedCostsPmt;
        }
        break;
      case 'dvp':
        params['gi_id'] = this.summaryData?.gi_code;
        if (this.selectedDvpTeam && this.selectedDvpTeam !== 'null') {
          params['dvp_team'] = this.selectedDvpTeam;
        }
        if (this.selectedDvpSnapshotDate && this.selectedDvpSnapshotDate !== 'null') {
          params['snapshot_date'] = this.selectedDvpSnapshotDate;
        }
        if (this.selectedCostsPmt && this.selectedCostsPmt !== 'null') {
          params['pmt_code'] = this.selectedCostsPmt;
        }
        break;
      case 'designRules':
        params['model_year'] = this.summaryData?.model_year?.toString();
        params['program_name'] = this.summaryData?.program_code;
        if (this.selectedCostsPmt && this.selectedCostsPmt !== 'null') {
          params['pmt_code'] = this.selectedCostsPmt;
        }
        break;
      case 'dpa5':
        params['gi_code'] = this.summaryData?.gi_code;
        if (this.selectedDpa5Cpsc && this.selectedDpa5Cpsc !== 'null') {
          params['cpsc'] = this.selectedDpa5Cpsc;
        }
        if (this.selectedDpa5Pmt && this.selectedDpa5Pmt !== 'null') {
          params['pmt'] = this.selectedDpa5Pmt;
        }
        if (this.selectedDpa5SnapshotDate && this.selectedDpa5SnapshotDate !== 'null') {
          params['snapshot_date'] = this.selectedDpa5SnapshotDate;
        }
        break;
      case 'hir':
        params['gi_code'] = this.summaryData?.gi_code;
        if (this.selectedProgram && this.selectedProgram !== 'null') {
          params['cpsc'] = this.selectedProgram;
        }
        if (this.selectedCostsPmt && this.selectedCostsPmt !== 'null') {
          params['pmt_code'] = this.selectedCostsPmt;
        }
        break;
      case 'costs':
        params['effectivein'] = this.summaryData?.parsed?.effective_point;
        if (this.selectedCostsCpsc && this.selectedCostsCpsc !== 'null') {
          params['cpsc'] = this.selectedCostsCpsc;
        }
        if (this.selectedCostsPmt && this.selectedCostsPmt !== 'null') {
          params['pmt_code'] = this.selectedCostsPmt;
        }
        params['cost_type'] = this.costsView === 'pieces' ? 'piece' : 'tooling';
        break;
    }

    return params;
  }

  get canExtractCurrentChart(): boolean {
    if (!this.hasValidSummary || !this.activeChart) return false;
    const config = this.chartExportConfig[this.activeChart];
    return config.enabled && !!config.endpointUrl;
  }

  get currentExtractLabel(): string {
    if (!this.activeChart) return 'Extract Data';
    return this.canExtractCurrentChart ? 'Extract Data' : `Extract ${this.activeChart.toUpperCase()} (Soon)`;
  }

  get userName(): string {
    return 'Demo Visitor';
  }

  constructor(
    private service: VehicleLineService,
    private fedeStatusService: FedeStatusService,
    private costsService: CostsService,
    private dpa5Service: Dpa5Service,
    private state: StateService,
    private toastService: ToastService,
    private dvpGlidepathService: DvpGlidepathService,
  ) {}

  ngOnInit() {
    this.state.activeChart$.subscribe(chart => {
      this.activeChart = chart;
    });

    this.state.selectedDvpTeam$.subscribe(team => {
      this.selectedDvpTeam = team;
    });

    this.state.selectedPmtCode$.subscribe(pmt => {
      const pmtChanged = pmt !== this.selectedDpa5Pmt;
      this.selectedCostsPmt = pmt;
      this.selectedDpa5Pmt = pmt;
      this.selectedDvpPmt = pmt;
      // Reload DPA5 CPSC list when PMT changes and we have a valid gi_code
      if (pmtChanged) {
        this.selectedDvpMilestone = null;
        this.selectedDpa5Cpsc = null;
        this.availableDpa5Cpscs = [];
        if (this.summaryData?.gi_code) {
          this.loadDvpTeams(this.summaryData.gi_code);
          this.loadCommodities(this.summaryData.gi_code);
          this.loadDrCpscList(this.summaryData.gi_code);
          if (pmt) {
            this.loadDpa5CpscList(this.summaryData.gi_code, pmt);
          }
        }
      }
    });
  }

  filterModelYears(event: any) {
    this.toastService.info('Loading...', 'Fetching model years');
    this.service.getModelYears(event.query).subscribe({
      next: (resp) => {
        // Date-time records do not map consistently to downstream filters.
        // Retain only numeric model-year representations such as YYYY or YYYY.25.
        const validModelYearPattern = /^\d{4}(\.\d+)?$/;
        const validYears = resp.filter(x => validModelYearPattern.test(x));
        this.filteredModelYears = validYears.map(x => ({ label: x, value: x }));
        this.toastService.success('Success!', `${validYears.length} year(s) found`);
      },
      error: (err) => {
        console.error(err);
        this.toastService.error('Error', 'Could not load model years');
      }
    });
  }

  filterProgramNames(event: any) {
    const modelYearVal = this.modelYear?.value || (typeof this.modelYear === 'string' ? this.modelYear : '');

    this.toastService.info('Loading...', 'Fetching program names');
    this.service.getProgramNames(event.query, modelYearVal || undefined).subscribe({
      next: (resp) => {
        this.filteredProgramNames = resp.map(x => ({ label: x, value: x }));
        this.toastService.success('Success!', `${resp.length} program(s) found`);
      },
      error: (err) => {
        console.error(err);
        this.toastService.error('Error', 'Could not load programs');
      }
    });
  }

  filterProgramCodes(event: any) {
    const modelYearVal = this.modelYear?.value || (typeof this.modelYear === 'string' ? this.modelYear : '');
    const programNameVal = this.programName?.value || (typeof this.programName === 'string' ? this.programName : '');

    this.toastService.info('Loading...', 'Fetching program codes');
    this.service.getProgramCodes(event.query, modelYearVal || undefined, programNameVal || undefined).subscribe({
      next: (resp) => {
        this.filteredProgramCodes = resp.map(x => ({ label: x, value: x }));
        this.toastService.success('Success!', `${resp.length} code(s) found`);
      },
      error: (err) => {
        console.error(err);
        this.toastService.error('Error', 'Could not load program codes');
      }
    });
  }

  clearFilters() {
    this.modelYear = null;
    this.programName = null;
    this.programCode = null;
  }

submitForm() {
  const modelYearVal = typeof this.modelYear === 'string'
    ? this.modelYear
    : this.modelYear?.value || '';
  const programNameVal = typeof this.programName === 'string'
    ? this.programName
    : this.programName?.value || '';
  const programCodeVal = typeof this.programCode === 'string'
    ? this.programCode
    : this.programCode?.value || '';

  // Required: model_year and program_codes
  if (!modelYearVal || !programCodeVal) {
    this.toastService.warning('Required Fields', 'Please fill Model Year and Program Code');
    return;
  }

  this.summaryData = null;
  this.hasValidSummary = false;
  this.isLoadingData = true;

  this.toastService.info('Processing...', 'Fetching summary data');

  // Updated parameter order: modelYear, programCodes, programNames (optional)
  this.service.getSummary(modelYearVal, programCodeVal, programNameVal || undefined)
    .subscribe({
      next: res => {
        // Validate response
        if (!res || !res.summary || !res.gi_code) {
          console.error('Invalid response from backend:', res);
          this.summaryData = null;
          this.hasValidSummary = false;
          this.isLoadingData = false;
          this.state.setVehicleName('None');
          this.state.setMilestones([]);
          this.toastService.error('Error', 'Invalid data received from server. Please try again.');
          return;
        }

        try {
          // The backend returns VehicleLineSchema directly.
          const parsed = this.parseSummary(res.summary, res.gi_code);

          this.summaryData = {
            summary: res.summary,
            milestones: res.milestones || {},
            parsed,
            gi_code: res.gi_code,
            program_code: res.program_code,
            vehicle_line: res.vehicle_line,
            affected_plant: res.affected_plant,
            plant_code: res.plant_code,
            model_year: res.model_year,
            wers_plant: res.wers_plant
          };

          this.hasValidSummary = !!this.summaryData && Object.keys(this.summaryData).length > 0;
          this.submitted = true;
          this.isLoadingData = false;

          if (this.hasValidSummary) {
            this.state.setVehicleName(parsed.vehicle_line || '');
            this.state.setGiCode(res.gi_code);
            const milestones = this.getNonNullMilestones();
            this.state.setMilestones(milestones);

            // Load DVP Teams for the selected GI Code
            this.loadDvpTeams(res.gi_code);

            // Load Commodities (CPSC programs) for CAE and HIR selects
            this.loadCommodities(res.gi_code);

            // Load CPSC codes for DR select
            this.loadDrCpscList(res.gi_code);

            // Load Costs CPSCs for effective point
            this.loadCostsCpscList(parsed.effective_point);

            // Load DPA5 CPSCs if a PMT is already selected
            if (this.selectedDpa5Pmt) {
              this.selectedDpa5Cpsc = null;
              this.availableDpa5Cpscs = [];
              this.loadDpa5CpscList(res.gi_code, this.selectedDpa5Pmt);
            }

            // Load DPA5 Snapshot Dates
            this.loadDpa5SnapshotDates(res.gi_code);

            // Load DVP Snapshot Dates
            this.loadDvpSnapshotDates(res.gi_code);

            this.toastService.success('Success!', `Data loaded for ${parsed.vehicle_line}`);
          }
        } catch (parseError) {
          console.error('Error parsing summary data:', parseError);
          this.summaryData = null;
          this.hasValidSummary = false;
          this.isLoadingData = false;
          this.state.setVehicleName('None');
          this.state.setMilestones([]);
          this.toastService.error('Error', 'Failed to process data. Please try again.');
        }
      },
      error: err => {
        console.error('Error fetching summary:', err);
        this.summaryData = null;
        this.hasValidSummary = false;
        this.isLoadingData = false;
        this.state.setVehicleName('None');
        this.state.setMilestones([]);

        const errorMsg = err?.error?.detail || err?.message || 'Unable to fetch data. Please verify your search criteria and try again.';
        this.toastService.error('Search Failed', errorMsg);
      }
    });
}

  private parseSummary(summary: string, giCode?: string): {
    vehicle_line: string;
    vehicle_ptvl: string;
    affected_plant: string;
    plant_code: string;
    effective_point: string;
    gi_code: string;
  } {
    if (!summary) {
      return {
        vehicle_line: '',
        vehicle_ptvl: '',
        affected_plant: '',
        plant_code: '',
        effective_point: '',
        gi_code: giCode || ''
      };
    }

    const parts: Record<string, string> = {};
    summary.split("|").forEach(part => {
      const [key, value] = part.split(":").map(p => p.trim());
      if (key && value) {
        parts[key.toLowerCase().replace(/ /g, "_")] = value;
      }
    });

    let vehicleLine = parts["project_description"] || "";
    const match = vehicleLine.match(/\(([^)]+)\)$/); // Capture the final parenthesized plant value.
    const affectedPlant = match ? match[1] : "";
    vehicleLine = vehicleLine.replace(/\s*\([^)]+\)$/, ""); // Remove the plant suffix from the vehicle line.

    return {
      vehicle_line: vehicleLine,
      vehicle_ptvl: parts["ptvl"] || "",
      affected_plant: affectedPlant,
      plant_code: parts["effective_point"] || "",
      effective_point: parts["effective_point"] || "",
      gi_code: giCode || ''
    };
  }

  extractPTVL(summary: string): string {
    if (!summary) return '';
    const parts = summary.split('|').map(p => p.trim());
    const ptvlPart = parts.find(p => p.startsWith('ptvl:'));
    return ptvlPart ? ptvlPart.replace('ptvl:', '').trim() : '';
  }

  getNonNullMilestones(): { key: string, value: any }[] {
    if (!this.summaryData?.milestones) return [];

    return Object.entries(this.summaryData.milestones)
      .filter(([_, value]) =>
        value && value !== "-" && value !== "NaT" && value !== "Invalid Date"
      )
      .map(([key, value]) => ({
        key,
        value
      }));
  }

  toggleKeyEngineering() {
    this.showKeyEngineering = !this.showKeyEngineering;
  }

  setActiveChart(chart: ChartType) {
    this.state.setActiveChart(chart);
  }

  onProgramChange() {
    // CAE totals react to program changes through the selectedProgram input.
    // Load HIR DVP Teams when commodity is selected
    this.selectedHirDvpTeam = null;
    if (this.selectedProgram && this.summaryData?.gi_code) {
      this.loadHirDvpTeams(this.summaryData.gi_code, this.selectedProgram);
    } else {
      this.availableHirDvpTeams = [];
    }
  }

  onHirDvpTeamChange() {
    // HIR metric components react to the selected DVP team through their inputs.
    if (this.selectedHirDvpTeam === 'null') {
      this.selectedHirDvpTeam = null;
    }
  }

  onDvpTeamChange() {
    if (this.selectedDvpTeam && this.selectedDvpTeam !== 'null') {
      this.state.setSelectedDvpTeam(this.selectedDvpTeam);
    } else {
      this.selectedDvpTeam = null;
      this.state.setSelectedDvpTeam(null);
    }
  }

  onDvpGlidepathPmtListChanged(pmts: string[]): void {
    this.dvpGlidepathPmtList = pmts;
  }

  onDvpGlidepathMilestoneListChanged(milestones: string[]): void {
    this.dvpGlidepathMilestoneList = milestones;
  }

  onDvpPmtChange(): void {
    this.selectedDvpMilestone = null;
    if (this.selectedDvpPmt === 'null') {
      this.selectedDvpPmt = null;
    }
    this.state.setSelectedPmtCode(this.selectedDvpPmt);
  }

  onDvpMilestoneChange(): void {
    if (this.selectedDvpMilestone === 'null') {
      this.selectedDvpMilestone = null;
    }
  }

  onDvpSnapshotChange(): void {
    if (this.selectedDvpSnapshotDate === 'null') {
      this.selectedDvpSnapshotDate = null;
    }
  }

  loadDvpSnapshotDates(giCode: string) {
    this.dvpGlidepathService.getSnapshots(giCode).subscribe({
      next: (res) => {
        let snapshots = res.snapshots || [];
        this.availableDvpSnapshotDates = snapshots;
        this.selectedDvpSnapshotDate = null;
      },
      error: (err) => {
        console.error('Error loading DVP snapshot dates', err);
        // Fallback to mock data on error for testing
        this.availableDvpSnapshotDates = [];
        this.selectedDvpSnapshotDate = null;
      }
    });
  }



  updateDvpChart(cpscCode: string | null) {
    this.selectedDvpCpsc = (cpscCode && cpscCode !== 'null') ? cpscCode : null;
  }

  setDvpView(view: 'assessment' | 'classification') {
    this.dvpView = view;
    if (view === 'classification' && this.availableDrCpscCodes.length > 0) {
      const initial = this.selectedDvpCpsc || this.availableDrCpscCodes[0];
      this.updateDvpChart(initial);
    }
  }

  setCostsView(view: 'pieces' | 'tooling') {
    this.costsView = view;
  }

  onDrCommodityChange() {
    if (this.selectedDrCommodity === 'null') {
      this.selectedDrCommodity = null;
    }
  }

  /**
   * Load DVP Teams filtered by GI Code from the backend
   * Uses the endpoint: /fede-status/dvp-teams/autocomplete/by-gi-code
   */
  loadDvpTeams(giCode: string) {
    if (!giCode) {
      this.availableDvpTeams = [];
      return;
    }

    this.fedeStatusService.getDvpTeamsByGiCode(giCode, undefined, this.selectedCostsPmt).subscribe({
      next: (teams) => {
        this.availableDvpTeams = teams;
        this.selectedDvpTeam = null; // Reset selection when new data loads
        console.log(`Loaded ${teams.length} DVP Teams for GI Code: ${giCode}`);
      },
      error: (err) => {
        console.error('Error loading DVP Teams:', err);
        this.availableDvpTeams = [];
        this.toastService.error('Error', 'Could not load DVP Teams');
      }
    });
  }

  /**
   * Load HIR DVP Teams filtered by GI Code and Program (commodity)
   * Uses the same endpoint as DVP Teams but can be extended for HIR-specific filtering
   */
  loadHirDvpTeams(giCode: string, program: string) {
    if (!giCode) {
      this.availableHirDvpTeams = [];
      return;
    }

    // Using the same DVP Teams endpoint - can be changed to HIR-specific endpoint if needed
    this.fedeStatusService.getDvpTeamsByGiCode(giCode, undefined, this.selectedCostsPmt).subscribe({
      next: (teams) => {
        this.availableHirDvpTeams = teams;
        this.selectedHirDvpTeam = null; // Reset selection when new data loads
        console.log(`Loaded ${teams.length} HIR DVP Teams for GI Code: ${giCode}, Program: ${program}`);
      },
      error: (err) => {
        console.error('Error loading HIR DVP Teams:', err);
        this.availableHirDvpTeams = [];
        this.toastService.error('Error', 'Could not load HIR DVP Teams');
      }
    });
  }

  loadCommodities(giCode: string) {
    if (!giCode) {
      this.availablePrograms = [];
      return;
    }

    this.service.getCommoditiesByGiCode(giCode, this.selectedCostsPmt).subscribe({
      next: (commodities) => {
        this.availablePrograms = commodities;
        this.selectedProgram = null;
        console.log(`Loaded ${commodities.length} commodities for GI Code: ${giCode}`);
      },
      error: (err) => {
        console.error('Error loading commodities:', err);
        this.availablePrograms = [];
        this.toastService.error('Error', 'Could not load commodities');
      }
    });
  }

  loadDrCpscList(giCode: string) {
    if (!giCode) {
      this.availableDrCpscCodes = [];
      return;
    }

    this.service.getCpscListByGiCode(giCode, this.selectedCostsPmt).subscribe({
      next: (codes) => {
        this.availableDrCpscCodes = codes;
        this.selectedDrCommodity = null;
        // Reset CPSC selection for new GI Code; auto-trigger chart if already in classification view
        this.selectedDvpCpsc = null;
        if (this.dvpView === 'classification' && codes.length > 0) {
          this.updateDvpChart(codes[0]);
        }
        console.log(`Loaded ${codes.length} CPSC codes for GI Code: ${giCode}`);
      },
      error: (err) => {
        console.error('Error loading CPSC list:', err);
        this.availableDrCpscCodes = [];
        this.selectedDvpCpsc = null;
      }
    });
  }

  /**
   * Load available CPSCs for Costs module
   */
  loadCostsCpscList(effectivePoint: string) {
    if (!effectivePoint) {
      this.availableCostsCpscs = [];
      return;
    }

    this.costsService.getCpscList(effectivePoint).subscribe({
      next: (response) => {
        this.availableCostsCpscs = response.cpsc_codes;
        this.selectedCostsCpsc = null;
        this.availableCostsPmts = [];
        this.loadCostsPmtList();
        console.log(`Loaded ${response.count} Costs CPSCs for Effective Point: ${effectivePoint}`);
      },
      error: (err) => {
        console.error('Error loading Costs CPSCs:', err);
        this.availableCostsCpscs = [];
        this.selectedCostsCpsc = null;
        this.toastService.error('Error', 'Could not load cost commodities');
      }
    });
  }

  /**
   * Load available PMTs from the general list (100, 200, 300, 400, 500, 600)
   */
  loadCostsPmtList() {
    this.costsService.getPmtGeneralList().subscribe({
      next: (response) => {
        this.availableCostsPmts = response.pmt_codes;
        this.selectedCostsPmt = this.state.getSelectedPmtCode();
      },
      error: (err) => {
        console.error('Error loading general PMT list:', err);
        this.availableCostsPmts = [];
        this.selectedCostsPmt = null;
      }
    });
  }

  /**
   * Handle changes to Costs CPSC selection
   */
  onCostsCpscChange() {
    if (this.selectedCostsCpsc === 'null') {
      this.selectedCostsCpsc = null;
    }
    // PMT list is the general static list — no reload needed on CPSC change
  }

  /**
   * Handle changes to Costs PMT selection
   */
  onCostsPmtChange() {
    if (this.selectedCostsPmt === 'null') {
      this.selectedCostsPmt = null;
    }
    this.state.setSelectedPmtCode(this.selectedCostsPmt);
  }

  /**
   * Load distinct CPSC codes available in DPA5 for the given GI Code + PMT
   */
  loadDpa5CpscList(giCode: string, pmt: string): void {
    this.isLoadingDpa5Cpscs = true;
    this.dpa5Service.getCpscList(giCode, pmt).subscribe({
      next: (resp) => {
        this.availableDpa5Cpscs = resp.cpsc_codes;
        this.isLoadingDpa5Cpscs = false;
      },
      error: () => {
        this.availableDpa5Cpscs = [];
        this.isLoadingDpa5Cpscs = false;
      }
    });
  }

  onDpa5CpscChange(): void {
    if (this.selectedDpa5Cpsc === 'null') {
      this.selectedDpa5Cpsc = null;
    }
  }

  loadDpa5SnapshotDates(giCode: string): void {
    if (!giCode) {
      this.availableDpa5SnapshotDates = [];
      return;
    }
    this.dpa5Service.getSnapshots(giCode).subscribe({
      next: (resp) => {
        let snapshots = resp.snapshots || [];
        this.availableDpa5SnapshotDates = snapshots;
        this.selectedDpa5SnapshotDate = null;
      },
      error: () => {
        // Fallback to mock data on error for testing
        this.availableDpa5SnapshotDates = ['2026-10-01', '2026-10-08', '2026-10-15'];
        this.selectedDpa5SnapshotDate = null;
      }
    });
  }

  onDpa5SnapshotChange(): void {
    if (this.selectedDpa5SnapshotDate === 'null') {
      this.selectedDpa5SnapshotDate = null;
    }
  }

}
