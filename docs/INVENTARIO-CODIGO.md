# Inventário verificável de contratos, transformações e consultas
Gerado dos arquivos desta versão. Código integral para rastrear cada parâmetro, campo e transformação. Não contém nem reconstrói SQL BigQuery ausente. Veja [o guia da pipeline](PIPELINE-ENTREVISTA.md).

## `front/dandr-web/src/app/dashboard/home/home.ts`

[Fonte](../front/dandr-web/src/app/dashboard/home/home.ts)

```ts
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

```

## `front/dandr-web/src/app/shared/state.service.ts`

[Fonte](../front/dandr-web/src/app/shared/state.service.ts)

```ts
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

/** Deliverable dashboard that is currently active. */
export type ChartType = 'dvp' | 'designRules' | 'cae' | 'hir' | 'costs' | 'dpa5' | null;

@Injectable({ providedIn: 'root' })
/** Central reactive store for cross-component dashboard selections. */
export class StateService {
  private vehicleNameSource = new BehaviorSubject<string>('None');
  vehicleName$ = this.vehicleNameSource.asObservable();

  private giCodeSource = new BehaviorSubject<string | null>(null);
  giCode$ = this.giCodeSource.asObservable();

  private milestonesSource = new BehaviorSubject<{ key: string, value: any }[]>([]);
  milestones$ = this.milestonesSource.asObservable();

  private activeChartSource = new BehaviorSubject<ChartType>('cae');
  activeChart$ = this.activeChartSource.asObservable();

  private selectedDvpTeamSource = new BehaviorSubject<string | null>(null);
  selectedDvpTeam$ = this.selectedDvpTeamSource.asObservable();

  private selectedMilestoneSource = new BehaviorSubject<string | null>(null);
  selectedMilestone$ = this.selectedMilestoneSource.asObservable();

  private selectedPmtCodeSource = new BehaviorSubject<string | null>(null);
  selectedPmtCode$ = this.selectedPmtCodeSource.asObservable();

  /** Update the selected vehicle display name. */
  setVehicleName(name: string) {
    this.vehicleNameSource.next(name);
  }

  /** Update the selected GI code. */
  setGiCode(code: string | null) {
    this.giCodeSource.next(code);
  }

  /** Replace the milestone timeline for the selected vehicle. */
  setMilestones(list: { key: string, value: any }[]) {
    this.milestonesSource.next(list);
  }

  /** Activate a deliverable dashboard. */
  setActiveChart(chartType: ChartType) {
    this.activeChartSource.next(chartType);
  }

  /** Return the current deliverable dashboard. */
  getActiveChart() {
    return this.activeChartSource.value;
  }

  /** Update the globally selected DVP team. */
  setSelectedDvpTeam(team: string | null) {
    this.selectedDvpTeamSource.next(team);
  }

  /** Return the globally selected DVP team. */
  getSelectedDvpTeam() {
    return this.selectedDvpTeamSource.value;
  }

  /** Update the globally selected milestone. */
  setSelectedMilestone(milestone: string | null) {
    this.selectedMilestoneSource.next(milestone);
  }

  /** Return the globally selected milestone. */
  getSelectedMilestone() {
    return this.selectedMilestoneSource.value;
  }

  /** Update the canonical PMT selected in the sidebar. */
  setSelectedPmtCode(pmt: string | null) {
    this.selectedPmtCodeSource.next(pmt);
  }

  /** Return the canonical PMT selected in the sidebar. */
  getSelectedPmtCode() {
    return this.selectedPmtCodeSource.value;
  }
}


```

## `front/dandr-web/src/app/services/costs.service.ts`

[Fonte](../front/dandr-web/src/app/services/costs.service.ts)

```ts
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

```

## `front/dandr-web/src/app/services/dpa5.service.ts`

[Fonte](../front/dandr-web/src/app/services/dpa5.service.ts)

```ts
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

```

## `front/dandr-web/src/app/services/dvp-glidepath.service.ts`

[Fonte](../front/dandr-web/src/app/services/dvp-glidepath.service.ts)

```ts
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

```

## `front/dandr-web/src/app/services/fede-status.service.ts`

[Fonte](../front/dandr-web/src/app/services/fede-status.service.ts)

```ts
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

```

## `front/dandr-web/src/app/services/milestone-readiness.service.ts`

[Fonte](../front/dandr-web/src/app/services/milestone-readiness.service.ts)

```ts
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

```

## `front/dandr-web/src/app/services/vehicle-line.service.ts`

[Fonte](../front/dandr-web/src/app/services/vehicle-line.service.ts)

```ts
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

```

## `back/app/controllers/summary_controller.py`

[Fonte](../back/app/controllers/summary_controller.py)

```py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.vehicle_line import VehicleLine
from app.models.effective_point import EffectivePoint
from app.models.key_datas import KeyDatas

def fetch_summary(db: Session, program_code: str, model_year: int, program_name: str):
    vehicle_line = (
        db.query(VehicleLine)
        .filter(
            VehicleLine.program_code == program_code,
            VehicleLine.model_year == model_year,
            VehicleLine.program_name == program_name
        )
        .first()
    )

    if not vehicle_line:
        raise HTTPException(status_code=404, detail="Vehicle line not found.")

    milestones = (
        db.query(EffectivePoint)
        .filter(EffectivePoint.vehicle_line_id == vehicle_line.id)
        .all()
    )

    vehicle_line_str = (
        f"{vehicle_line.model_year}MY {vehicle_line.program_code} "
        f"{vehicle_line.program_name} ({vehicle_line.tg_code}) - {vehicle_line.effective_point}"
    )

    summary_text = (
        vehicle_line.summary
        or f"Resumo do programa {vehicle_line.program_name} ({vehicle_line.program_code}), "
           f"fase {vehicle_line.effective_point}, em {vehicle_line.affected_plant}."
    )

    return {
        "vehicle_line": vehicle_line_str,
        "affected_plant": vehicle_line.affected_plant,
        "plant_code": vehicle_line.plant_code,
        "summary": summary_text,
        "key_datas": [
            {
                "milestone": m.milestone_name,
                "date": m.milestone_date.isoformat() if m.milestone_date else None,
                "status": m.status
            }
            for m in milestones
        ]
    }

```

## `back/app/controllers/vehicle_line_controller.py`

[Fonte](../back/app/controllers/vehicle_line_controller.py)

```py
from app.services.vehicle_line_service import get_vehicle_line_summary

def fetch_vehicle_line_summary(program_code: str, model_year: int, program_name: str):
    """
    Controller responsável por orquestrar a obtenção do resumo do Vehicle Line.
    """
    return get_vehicle_line_summary(program_code, model_year, program_name)

```

## `back/app/services/summary_service.py`

[Fonte](../back/app/services/summary_service.py)

```py
from sqlalchemy.orm import Session
from app.models.vehicle_line import VehicleLine

def get_vehicle_summary(db: Session, program_code: str, program_name: str, model_year: int):
    vehicle = (
        db.query(VehicleLine)
        .filter(
            VehicleLine.program_code == program_code,
            VehicleLine.program_name == program_name,
            VehicleLine.model_year == model_year
        )
        .first()
    )

    if not vehicle:
        return None

    summary = {
        "vehicle_line": f"{vehicle.model_year}MY {vehicle.program_code} {vehicle.program_name} - {vehicle.effective_point}",
        "affected_plant": vehicle.affected_plant,
        "plant_code": vehicle.plant_code,
        "key_datas": [
            {"event": kd.event, "date": kd.date.strftime("%Y-%m-%d")}
            for kd in getattr(vehicle, "key_datas", [])
        ],
    }

    return summary

```

## `back/app/services/vehicle_line_service.py`

[Fonte](../back/app/services/vehicle_line_service.py)

```py
from app.schemas.vehicle_line import VehicleLineSchema

def get_vehicle_line_summary(program_code: str, model_year: int, program_name: str):
    """
    Simulando a consolidação dos dados. Em um cenário real, aqui serão consultas via SQL 
    às tabelas vpp001_glb_integrator_prj_vw, vpp002_mfg_veh_pgm_vw, vpp005_prj_timing_pivot_vw, etc.
    """

    mock_effective_point = "S4PVBS"
    mock_affected_plant = "Michigan Assembly Plant"
    mock_plant_code = "NA02"

    vehicle_line = f"{model_year} {program_code} {program_name}"
    summary = f"{vehicle_line} ({mock_affected_plant.split()[0]}) - {mock_effective_point}"

    return VehicleLineSchema(
        program_code=program_code,
        model_year=model_year,
        program_name=program_name,
        vehicle_line=vehicle_line,
        affected_plant=mock_affected_plant,
        plant_code=mock_plant_code,
        summary=summary,
        effective_point={"effective_point": mock_effective_point}
    )

```

## `back/app/routes/key_datas_routes.py`

[Fonte](../back/app/routes/key_datas_routes.py)

```py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.key_datas import KeyDatas
from app.schemas.key_datas import KeyDataSchema
from app.core.database import SessionLocal
from typing import List

router = APIRouter(prefix="/key-datas", tags=["Key Datas"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[KeyDataSchema])
def list_key_datas(effective_point_id: int = None, db: Session = Depends(get_db)):
    query = db.query(KeyDatas)
    if effective_point_id:
        query = query.filter(KeyDatas.effective_point_id == effective_point_id)
    return query.all()

```

## `back/app/models/effective_point.py`

[Fonte](../back/app/models/effective_point.py)

```py
from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base

class EffectivePoint(Base):
    __tablename__ = "effective_point"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_line_id = Column(Integer, ForeignKey("vehicle_lines.id"), unique=True)
    effective_point = Column(String)
    status = Column(String)

    vehicle_line = relationship("VehicleLine", back_populates="effective_point", uselist=False)

```

## `back/app/models/key_datas.py`

[Fonte](../back/app/models/key_datas.py)

```py
from sqlalchemy import Column, Date, ForeignKey, Integer, String
from app.core.database import Base

class KeyDatas(Base):
    __tablename__ = "key_datas"

    id = Column(Integer, primary_key=True, index=True)
    effective_point_id = Column(Integer, ForeignKey("effective_point.id"))
    milestone_name = Column(String)
    milestone_date = Column(Date)

```

## `back/app/models/vehicle_line.py`

[Fonte](../back/app/models/vehicle_line.py)

```py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class VehicleLine(Base):
    __tablename__ = "vehicle_lines"

    id = Column(Integer, primary_key=True, index=True)
    program_code = Column(String, index=True)
    model_year = Column(Integer)
    program_name = Column(String, index=True)
    vehicle_line = Column(String)
    affected_plant = Column(String)
    plant_code = Column(String)
    summary = Column(String)
    effective_point = relationship(
        "EffectivePoint",
        back_populates="vehicle_line",
        uselist=False,
        cascade="all, delete-orphan"
    )

```

## `back/app/schemas/effective_point.py`

[Fonte](../back/app/schemas/effective_point.py)

```py
from pydantic import BaseModel
from typing import Optional

class EffectivePointSchema(BaseModel):
    id: Optional[int] = None
    effective_point: str
    status: Optional[str] = None

    model_config = {"from_attributes": True}


```

## `back/app/schemas/key_datas.py`

[Fonte](../back/app/schemas/key_datas.py)

```py
from pydantic import BaseModel
from datetime import date
from typing import Optional

class KeyDataSchema(BaseModel):
    id: Optional[int] = None
    effective_point_id: int
    milestone_name: str
    milestone_date: date

    model_config = {"from_attributes": True}


```

## `back/app/schemas/summary.py`

[Fonte](../back/app/schemas/summary.py)

```py
from pydantic import BaseModel
from typing import List, Optional

class KeyData(BaseModel):
    event: str
    date: str

class VehicleLineSummary(BaseModel):
    vehicle_line: str  
    affected_plant: str 
    plant_code: str  
    key_datas: Optional[List[KeyData]] = None

    model_config = {"from_attributes": True}


```

## `back/app/schemas/vehicle_line.py`

[Fonte](../back/app/schemas/vehicle_line.py)

```py
from pydantic import BaseModel
from typing import Optional
from app.schemas.effective_point import EffectivePointSchema

class VehicleLineSchema(BaseModel):
    id: Optional[int] = None
    program_code: str
    model_year: int
    program_name: str
    vehicle_line: str
    affected_plant: str
    plant_code: str
    summary: str
    effective_point: Optional[EffectivePointSchema] = None

    model_config = {"from_attributes": True}

```

## `front/dandr-web/src/app/dashboard/components/cae-metrics/cae-metrics.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/cae-metrics/cae-metrics.ts)

```ts
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { VehicleLineService } from '../../../services/vehicle-line.service';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';

interface CaeData {
  program: string;
  total_assessments: number;
  meet: number;
  unassessed: number;
  approved_deviation: number;
  does_not_meet: number;
  co: number;
  carryover?: number;
}

@Component({
  selector: 'app-cae-metrics',
  standalone: true,
  imports: [DonutMetricsChartComponent],
  template: `
    <app-donut-metrics-chart
      [isLoading]="isLoading"
      [hasData]="hasData"
      [chartData]="chartData"
      [chartOptions]="chartOptions"
      [total]="totalAssessments"
      totalLabel="Total"
      [legendItems]="legendItems"
      [metricsData]="metricsData"
      [emptyMessage]="emptyMessage"
      [chartSize]="260">
    </app-donut-metrics-chart>
  `,
  styleUrl: './cae-metrics.scss'
})
/** Present the CAE metric summary for the current vehicle filters. */
export class CaeMetricsComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedProgram: string | null = null;
  @Input() selectedPmt: string | null = null;

  hasData = false;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  emptyMessage = 'No data available';
  metricsData: MetricCardData[] = [];
  legendItems: DonutLegendItem[] = [];

  metrics = {
    meet: 0, unassessed: 0, approved_deviation: 0,
    does_not_meet: 0, carryover: 0,
  };
  totalAssessments = 0;

  private readonly COLORS = ['#00B050', '#FFC000', '#FF9900', '#FF0000', '#808080'];
  private readonly LABELS = ['Meet', 'Unassessed', 'Approved Deviation', 'Does Not Meet', 'CO'];

  constructor(private vehicleLineService: VehicleLineService) {
    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: { enabled: true } }
    };
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.giCode) return;
    if (changes['giCode'] || changes['selectedProgram'] || changes['selectedPmt']) {
      this.loadData();
    }
  }

  loadData() {
    if (!this.giCode) return;
    this.isLoading = true;
    this.hasData = false;
    this.emptyMessage = this.selectedProgram
      ? `No data available for ${this.selectedProgram}`
      : 'No data available';

    this.vehicleLineService
      .getCaeTotalAssessments(this.giCode, this.selectedProgram || undefined, this.selectedPmt)
      .subscribe({
        next: (response: any) => {
          const rawData: CaeData[] = response.data || [];
          if (rawData.length > 0) {
            const agg = rawData.reduce(
              (acc, item) => ({
                meet: acc.meet + item.meet,
                unassessed: acc.unassessed + item.unassessed,
                approved_deviation: acc.approved_deviation + item.approved_deviation,
                does_not_meet: acc.does_not_meet + item.does_not_meet,
                carryover: acc.carryover + (item.carryover || 0),
                total_assessments: acc.total_assessments + item.total_assessments,
              }),
              { meet: 0, unassessed: 0, approved_deviation: 0, does_not_meet: 0, carryover: 0, total_assessments: 0 }
            );
            this.metrics = {
              meet: agg.meet, unassessed: agg.unassessed,
              approved_deviation: agg.approved_deviation, does_not_meet: agg.does_not_meet,
              carryover: agg.carryover,
            };
            this.totalAssessments = agg.total_assessments;
            this.buildData();
            this.hasData = true;
          }
          this.isLoading = false;
        },
        error: () => { this.isLoading = false; }
      });
  }

  buildData() {
    const values = [
      this.metrics.meet, this.metrics.unassessed, this.metrics.approved_deviation,
      this.metrics.does_not_meet, this.metrics.carryover,
    ];
    this.metricsData = [
      { label: 'Total Assessments', value: this.totalAssessments },
      ...this.LABELS.map((label, i) => ({
        label,
        value: values[i],
        percent: this.totalAssessments ? Math.round((values[i] / this.totalAssessments) * 100) : 0,
        color: ['meet', 'unassessed', 'approved-deviation', 'does-not-meet', 'cannot-assess'][i]
      }))
    ];
    this.legendItems = this.LABELS.map((label, i) => ({
      label,
      value: values[i],
      pct: this.totalAssessments ? ((values[i] / this.totalAssessments) * 100).toFixed(1) : '0',
      color: this.COLORS[i]
    }));
    this.chartData = {
      labels: this.LABELS,
      datasets: [{
        data: values,
        backgroundColor: this.COLORS,
        borderColor: '#FFFFFF',
        borderWidth: 2,
      }]
    };
  }
}

```

## `front/dandr-web/src/app/dashboard/components/dvp-total/dvp-total.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/dvp-total/dvp-total.ts)

```ts
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FedeStatusService } from '../../../services/fede-status.service';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';

@Component({
  selector: 'app-dvp-total',
  standalone: true,
  imports: [DonutMetricsChartComponent],
  template: `
    <app-donut-metrics-chart
      [isLoading]="isLoading"
      [hasData]="hasData"
      [chartData]="chartData"
      [chartOptions]="chartOptions"
      [total]="totalAssessments"
      totalLabel="Total"
      [legendItems]="legendItems"
      [metricsData]="metricsData"
      [emptyMessage]="emptyMessage"
      [chartSize]="260">
    </app-donut-metrics-chart>
  `,
  styleUrl: './dvp-total.scss'
})
/** Display aggregate DVP assessment-state totals. */
export class DvpTotalComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedDvpTeam: string | null = null;
  @Input() snapshotDate: string | null = null;
  @Input() selectedPmt: string | null = null;

  hasData = false;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  errorMessage: string | null = null;
  emptyMessage = 'No data available';
  metricsData: MetricCardData[] = [];
  legendItems: { label: string; value: number; pct: string; color: string }[] = [];

  metrics = {
    meet: 0, unassessed: 0, does_not_meet: 0,
    cannot_assess: 0, not_applicable: 0, approved_deviation: 0
  };
  totalAssessments = 0;

  private readonly COLORS = ['#00B050', '#FFC000', '#FF9900', '#FF0000', '#808080', '#CCCCCC'];
  private readonly LABELS = ['Meet', 'Unassessed', 'Approved Deviation', 'Does Not Meet', 'Cannot Assess', 'Not Applicable'];

  constructor(private fedeStatusService: FedeStatusService) {
    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: { enabled: true } }
    };
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.giCode) return;
    if (changes['giCode'] || changes['selectedDvpTeam'] || changes['snapshotDate'] || changes['selectedPmt']) {
      this.selectedDvpTeam ? this.loadTeamData() : this.loadTotalData();
    }
  }

  loadTotalData() {
    this.isLoading = true; this.hasData = false; this.errorMessage = null;
    this.emptyMessage = 'No data available';
    this.fedeStatusService.getConfStateMetrics(this.giCode!, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r: any) => { this.processMetrics(r?.conf_state_summary || {}); this.isLoading = false; },
      error: () => {
        this.processMetrics({ 'Meet': 120, 'Unassessed': 45, 'Approved Deviation': 28, 'Does Not Meet': 15, 'Cannot Assess': 8, 'Not Applicable': 4 });
        this.isLoading = false;
      }
    });
  }

  loadTeamData() {
    this.isLoading = true; this.hasData = false;
    this.emptyMessage = `No data for ${this.selectedDvpTeam}`;
    this.fedeStatusService.getDvpTeamListMetrics(this.giCode!, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r: any) => {
        const match = (r?.dvp_teams_metrics || []).find(
          (t: any) => (t?.dvp_team || '').toLowerCase() === this.selectedDvpTeam!.toLowerCase()
        );
        match ? this.processMetrics(match.conf_state_summary || {}) : (this.hasData = false);
        this.isLoading = false;
      },
      error: () => { this.hasData = false; this.isLoading = false; }
    });
  }

  processMetrics(s: Record<string, number>) {
    this.metrics = {
      meet:               s['Meet']               || s['meet']               || 0,
      unassessed:         s['Unassessed']         || s['unassessed']         || 0,
      does_not_meet:      s['Does Not Meet']      || s['does_not_meet']      || 0,
      cannot_assess:      s['Cannot Assess']      || s['cannot_assess']      || 0,
      not_applicable:     s['Not Applicable']     || s['not_applicable']     || 0,
      approved_deviation: s['Approved Deviation'] || s['approved_deviation'] || 0
    };
    this.totalAssessments = Object.values(this.metrics).reduce((a, b) => a + b, 0);
    const vals = [
      this.metrics.meet, this.metrics.unassessed, this.metrics.approved_deviation,
      this.metrics.does_not_meet, this.metrics.cannot_assess, this.metrics.not_applicable
    ];
    this.legendItems = this.LABELS.map((label, i) => ({
      label,
      value: vals[i],
      pct: this.totalAssessments === 0 ? '0.0' : ((vals[i] / this.totalAssessments) * 100).toFixed(1),
      color: this.COLORS[i]
    })).filter(item => item.value > 0);
    this.metricsData = [
      { label: 'Meet',               value: this.metrics.meet,               color: 'meet' },
      { label: 'Unassessed',         value: this.metrics.unassessed,         color: 'unassessed' },
      { label: 'Approved Deviation', value: this.metrics.approved_deviation, color: 'approved-deviation' },
      { label: 'Does Not Meet',      value: this.metrics.does_not_meet,      color: 'does-not-meet' },
      { label: 'Cannot Assess',      value: this.metrics.cannot_assess,      color: 'cannot-assess' },
      { label: 'Not Applicable',     value: this.metrics.not_applicable,     color: 'not-applicable' },
    ];
    this.chartData = {
      labels: this.LABELS,
      datasets: [{ data: vals, backgroundColor: this.COLORS, borderColor: this.COLORS, borderWidth: 0 }]
    };
    this.hasData = true;
  }

  calcPct(value: number): string {
    if (this.totalAssessments === 0) return '0.0';
    return ((value / this.totalAssessments) * 100).toFixed(1);
  }
}

```

## `front/dandr-web/src/app/dashboard/components/dvp-classification/dvp-classification.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/dvp-classification/dvp-classification.ts)

```ts
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FedeStatusService } from '../../../services/fede-status.service';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';

@Component({
  selector: 'app-dvp-classification',
  standalone: true,
  imports: [DonutMetricsChartComponent],
  template: `
    <app-donut-metrics-chart
      [isLoading]="isLoading"
      [hasData]="hasData"
      [chartData]="chartData"
      [chartOptions]="chartOptions"
      [total]="totalAssessments"
      totalLabel="Total"
      [legendItems]="legendItems"
      [metricsData]="metricsData"
      [emptyMessage]="emptyMessage"
      [chartSize]="260">
    </app-donut-metrics-chart>
  `
})
/** Visualize classified and unclassified DVP requirements. */
export class DvpClassificationComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedDvpTeam: string | null = null;
  @Input() selectedCpsc: string | null = null;
  @Input() snapshotDate: string | null = null;
  @Input() selectedPmt: string | null = null;

  hasData = false;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  emptyMessage = 'Select a CPSC to view classification data';
  metricsData: MetricCardData[] = [];
  legendItems: DonutLegendItem[] = [];
  totalAssessments = 0;

  // Colors/labels for CPSC classification view (2 slices)
  private readonly CPSC_COLORS = ['#00B050', '#FF0000'];
  private readonly CPSC_LABELS = ['Classified', 'Not Classified'];

  // Colors/labels for conf_state view (6 slices)
  private readonly COLORS = ['#00B050', '#FFC000', '#FF9900', '#FF0000', '#808080', '#CCCCCC'];
  private readonly LABELS = ['Meet', 'Unassessed', 'Approved Deviation', 'Does Not Meet', 'Cannot Assess', 'Not Applicable'];

  constructor(private fedeStatusService: FedeStatusService) {
    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: { enabled: true } }
    };
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.giCode) return;

    if (changes['selectedCpsc'] || changes['snapshotDate'] || changes['selectedPmt']) {
      const cpsc = this.selectedCpsc;
      if (cpsc && cpsc !== 'null') {
        this.loadClassificationMetrics(cpsc);
      } else {
        this.resetChart('Select a CPSC to view classification data');
      }
      return;
    }

    if (changes['giCode'] || changes['selectedDvpTeam'] || changes['snapshotDate']) {
      // If a CPSC is already selected, reload classification metrics
      if (this.selectedCpsc && this.selectedCpsc !== 'null') {
        this.loadClassificationMetrics(this.selectedCpsc);
        return;
      }
      this.selectedDvpTeam && this.selectedDvpTeam !== 'null'
        ? this.loadTeamData()
        : this.loadTotalData();
    }
  }

  loadClassificationMetrics(cpsc: string) {
    if (!this.giCode) return;
    this.isLoading = true;
    this.hasData = false;
    this.chartData = null;   // clear stale data before new request
    this.emptyMessage = `No classification data for CPSC: ${cpsc}`;

    this.fedeStatusService.getDvpClassification(this.giCode, cpsc, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r) => {
        const classified = r?.classified ?? 0;
        const notClassified = r?.not_classified ?? 0;
        const total = r?.total ?? (classified + notClassified);

        if (total === 0) {
          this.resetChart(`No data for CPSC: ${cpsc}`);
          this.isLoading = false;
          return;
        }

        this.totalAssessments = total;
        const pct = (v: number) => total === 0 ? '0.0' : ((v / total) * 100).toFixed(1);

        this.legendItems = [
          { label: 'Classified',     value: classified,    pct: pct(classified),    color: this.CPSC_COLORS[0] },
          { label: 'Not Classified', value: notClassified, pct: pct(notClassified), color: this.CPSC_COLORS[1] },
        ].filter(item => item.value > 0);

        this.metricsData = [
          { label: 'Classified',     value: classified,    color: 'meet' },
          { label: 'Not Classified', value: notClassified, color: 'does-not-meet' },
        ];

        this.chartData = {
          labels: this.CPSC_LABELS,
          datasets: [{
            data: [classified, notClassified],
            backgroundColor: this.CPSC_COLORS,
            borderColor: this.CPSC_COLORS,
            borderWidth: 0
          }]
        };

        this.hasData = true;
        this.isLoading = false;
      },
      error: () => {
        this.resetChart('Error loading classification data');
        this.isLoading = false;
      }
    });
  }

  loadTotalData() {
    this.isLoading = true;
    this.hasData = false;
    this.emptyMessage = 'No classification data available';
    this.fedeStatusService.getConfStateMetrics(this.giCode!, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r: any) => {
        this.processMetrics(r?.conf_state_summary || {});
        this.isLoading = false;
      },
      error: () => { this.resetChart('No classification data available'); this.isLoading = false; }
    });
  }

  loadTeamData() {
    this.isLoading = true;
    this.hasData = false;
    this.emptyMessage = `No classification data for ${this.selectedDvpTeam}`;
    this.fedeStatusService.getDvpTeamListMetrics(this.giCode!, this.snapshotDate, this.selectedPmt).subscribe({
      next: (r: any) => {
        const match = (r?.dvp_teams_metrics || []).find(
          (t: any) => (t?.dvp_team || '').toLowerCase() === this.selectedDvpTeam!.toLowerCase()
        );
        match ? this.processMetrics(match.conf_state_summary || {}) : this.resetChart(this.emptyMessage);
        this.isLoading = false;
      },
      error: () => { this.resetChart(this.emptyMessage); this.isLoading = false; }
    });
  }

  private resetChart(message: string) {
    this.hasData = false;
    this.totalAssessments = 0;
    this.legendItems = [];
    this.metricsData = [];
    this.chartData = null;
    this.emptyMessage = message;
  }

  processMetrics(s: Record<string, number>) {
    const m = {
      meet:               s['Meet']               || s['meet']               || 0,
      unassessed:         s['Unassessed']         || s['unassessed']         || 0,
      does_not_meet:      s['Does Not Meet']      || s['does_not_meet']      || 0,
      cannot_assess:      s['Cannot Assess']      || s['cannot_assess']      || 0,
      not_applicable:     s['Not Applicable']     || s['not_applicable']     || 0,
      approved_deviation: s['Approved Deviation'] || s['approved_deviation'] || 0,
    };
    this.totalAssessments = Object.values(m).reduce((a, b) => a + b, 0);
    const vals = [m.meet, m.unassessed, m.approved_deviation, m.does_not_meet, m.cannot_assess, m.not_applicable];
    const pct = (v: number) => this.totalAssessments === 0 ? '0.0' : ((v / this.totalAssessments) * 100).toFixed(1);

    this.legendItems = this.LABELS.map((label, i) => ({
      label, value: vals[i], pct: pct(vals[i]), color: this.COLORS[i]
    })).filter(item => item.value > 0);

    this.metricsData = [
      { label: 'Meet',               value: m.meet,               color: 'meet' },
      { label: 'Unassessed',         value: m.unassessed,         color: 'unassessed' },
      { label: 'Approved Deviation', value: m.approved_deviation, color: 'approved-deviation' },
      { label: 'Does Not Meet',      value: m.does_not_meet,      color: 'does-not-meet' },
      { label: 'Cannot Assess',      value: m.cannot_assess,      color: 'cannot-assess' },
      { label: 'Not Applicable',     value: m.not_applicable,     color: 'not-applicable' },
    ];

    this.chartData = {
      labels: this.LABELS,
      datasets: [{ data: vals, backgroundColor: this.COLORS, borderColor: this.COLORS, borderWidth: 0 }]
    };
    this.hasData = true;
  }
}

```

## `front/dandr-web/src/app/dashboard/components/dvp-glidepath/dvp-glidepath.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/dvp-glidepath/dvp-glidepath.ts)

```ts
import { Component, Input, OnInit, OnChanges, SimpleChanges, OnDestroy, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgApexchartsModule } from 'ng-apexcharts';
import type {
  ApexAxisChartSeries,
  ApexChart,
  ApexXAxis,
  ApexYAxis,
  ApexLegend,
  ApexTooltip,
  ApexAnnotations,
  ApexDataLabels,
  ApexStroke,
  ApexFill
} from 'ng-apexcharts';
import { LoadingSpinnerComponent } from '../../../shared/components/loading-spinner/loading-spinner';
import { DvpGlidepathService, DvpGlidepathRecord } from '../../../services/dvp-glidepath.service';
import { Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-dvp-glidepath',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule, LoadingSpinnerComponent],
  templateUrl: './dvp-glidepath.html',
  styleUrl: './dvp-glidepath.scss',
})
/** Render DVP completion timelines and expose available chart filters. */
export class DvpGlidepathComponent implements OnInit, OnChanges, OnDestroy {
  @Input() giCode: string | null = null;
  @Input() selectedPmt: string | null = null;
  @Input() selectedMilestone: string | null = null;
  @Input() snapshotDate: string | null = null;

  @Output() pmtListChanged = new EventEmitter<string[]>();
  @Output() milestoneListChanged = new EventEmitter<string[]>();

  private destroy$ = new Subject<void>();

  // Chart state
  hasChartData = false;
  isLoadingGlidepath = false;
  errorMessage: string | null = null;

  apexSeries: ApexAxisChartSeries = [];
  apexChart: ApexChart = {
    type: 'line',
    height: 420,
    stacked: false,
    toolbar: { show: true },
    zoom: { enabled: false },
    animations: { enabled: true }
  };
  apexXAxis: ApexXAxis = {
    type: 'datetime',
    labels: {
      format: 'dd-MMM-yyyy',
      rotate: -45,
      rotateAlways: true,
      style: { fontSize: '10px', colors: '#6c757d' },
      datetimeUTC: false
    },
    title: {
      text: 'Date',
      style: { color: '#495057', fontWeight: '600', fontSize: '13px' }
    }
  };
  apexYAxis: ApexYAxis = {
    min: 0,
    max: 100,
    labels: {
      formatter: (val: number) => `${val.toFixed(0)}%`,
      style: { colors: '#6c757d', fontSize: '12px' }
    },
    title: {
      text: '% Completion',
      style: { color: '#495057', fontWeight: '600', fontSize: '13px' }
    }
  };
  apexColors: string[] = ['#28a745', '#FF9800'];
  apexStroke: ApexStroke = { width: [2.5, 2.5], curve: 'smooth' };
  apexDataLabels: ApexDataLabels = { enabled: false };
  apexLegend: ApexLegend = { show: false };
  apexTooltip: ApexTooltip = {
    shared: true,
    intersect: false,
    x: { format: 'dd-MMM-yyyy' },
    y: { formatter: (val: number) => val != null ? `${Math.round(val)}%` : 'N/A' }
  };
  apexFill: ApexFill = { opacity: [1, 1] };
  apexAnnotations: ApexAnnotations = {};

  constructor(private glidepathService: DvpGlidepathService) {}

  ngOnInit(): void {
    if (this.giCode) {
      this.fetchPmtsAndLoad();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['giCode'] && !changes['giCode'].firstChange && changes['giCode'].currentValue) {
      this.fetchPmtsAndLoad();
    } else if (changes['selectedPmt'] && !changes['selectedPmt'].firstChange) {
      this.fetchMilestonesAndLoad();
    } else if (changes['selectedMilestone'] && !changes['selectedMilestone'].firstChange) {
      this.loadData();
    } else if (changes['snapshotDate'] && !changes['snapshotDate'].firstChange) {
      this.loadData();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private fetchPmtsAndLoad(): void {
    if (!this.giCode) return;
    this.glidepathService.getPmts(this.giCode)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (pmts) => {
          this.pmtListChanged.emit(pmts);
          this.loadData();
        },
        error: () => {
          this.pmtListChanged.emit([]);
          this.loadData();
        }
      });
  }

  private fetchMilestonesAndLoad(): void {
    if (!this.giCode || !this.selectedPmt) {
      this.milestoneListChanged.emit([]);
      this.loadData();
      return;
    }
    this.glidepathService.getMilestones(this.giCode, this.selectedPmt)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (milestones) => {
          this.milestoneListChanged.emit(milestones);
          this.loadData();
        },
        error: () => {
          this.milestoneListChanged.emit([]);
          this.loadData();
        }
      });
  }

  loadGlidepathData(): void {
    this.loadData();
  }

  private loadData(): void {
    if (!this.giCode) return;

    this.isLoadingGlidepath = true;
    this.errorMessage = null;
    this.hasChartData = false;

    this.glidepathService.getData(this.giCode, this.selectedPmt, this.selectedMilestone, this.snapshotDate)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (records) => {
          this.buildCumulativeSeries(records);
          this.isLoadingGlidepath = false;
        },
        error: (err) => {
          this.errorMessage = 'Failed to load glidepath data';
          this.isLoadingGlidepath = false;
          console.error('DVP Glidepath error:', err);
        }
      });
  }

  private buildCumulativeSeries(records: DvpGlidepathRecord[]): void {
    if (records.length === 0) {
      this.hasChartData = false;
      return;
    }

    const total = records.length;

    // Scheduled series — cumulative % by scheduled_finished date
    const scheduledSorted = records
      .filter(r => r.scheduled_finished)
      .sort((a, b) => a.scheduled_finished!.localeCompare(b.scheduled_finished!));

    const scheduledRaw = scheduledSorted.map((r, i) => ({
      x: new Date(r.scheduled_finished!).getTime(),
      y: Math.round((i + 1) / total * 100)
    }));

    // Deduplicate: same date keeps the highest y (last in sorted order)
    const scheduledMap = new Map<number, number>();
    for (const pt of scheduledRaw) {
      scheduledMap.set(pt.x, pt.y);
    }
    const scheduledData = Array.from(scheduledMap.entries())
      .map(([x, y]) => ({ x, y }))
      .sort((a, b) => a.x - b.x);

    // Actual series — cumulative % by actual_finished date (nulls ignored)
    const actualSorted = records
      .filter(r => r.actual_finished)
      .sort((a, b) => a.actual_finished!.localeCompare(b.actual_finished!));

    const actualRaw = actualSorted.map((r, i) => ({
      x: new Date(r.actual_finished!).getTime(),
      y: Math.round((i + 1) / total * 100)
    }));

    // Deduplicate: same date keeps the highest y
    const actualMap = new Map<number, number>();
    for (const pt of actualRaw) {
      actualMap.set(pt.x, pt.y);
    }
    const actualData = Array.from(actualMap.entries())
      .map(([x, y]) => ({ x, y }))
      .sort((a, b) => a.x - b.x);

    // Milestone vertical annotation — only when a milestone filter is active.
    // The date comes from the records returned by the API (already filtered).
    const milestoneDate = this.selectedMilestone
      ? (records.find(r => r.milestone)?.milestone ?? null)
      : null;
    if (milestoneDate) {
      this.apexAnnotations = {
        xaxis: [{
          x: new Date(milestoneDate).getTime(),
          borderColor: '#1E40AF',
          borderWidth: 2,
          strokeDashArray: 0,
          label: {
            text: `Milestone: ${this.formatDate(milestoneDate)}`,
            borderColor: '#1E40AF',
            style: {
              color: '#fff',
              background: '#1E40AF',
              fontSize: '11px',
              fontWeight: '600',
              padding: { left: 6, right: 6, top: 3, bottom: 3 }
            },
            orientation: 'vertical',
            position: 'top',
            offsetY: 0
          }
        }]
      };
    } else {
      this.apexAnnotations = {};
    }

    this.apexSeries = [
      { name: 'Scheduled Finished', data: scheduledData },
      { name: 'Actual Finished', data: actualData }
    ];

    this.hasChartData = true;
  }

  private formatDate(dateStr: string): string {
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    const d = new Date(+parts[0], +parts[1] - 1, +parts[2]);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  }
}

```

## `front/dandr-web/src/app/dashboard/components/design-rules-chart/design-rules-chart.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/design-rules-chart/design-rules-chart.ts)

```ts
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import Chart from 'chart.js/auto';
import { LoadingSpinnerComponent } from '../../../shared/components/loading-spinner';
import { VehicleLineService } from '../../../services/vehicle-line.service';
import { MetricsGridComponent, MetricCardData } from '../../../shared/components/metrics-chart-module';

@Component({
  selector: 'app-design-rules-chart',
  standalone: true,
  imports: [CommonModule, ChartModule, LoadingSpinnerComponent, MetricsGridComponent],
  templateUrl: './design-rules-chart.html',
  styleUrl: './design-rules-chart.scss',
})
/** Render Design Rule classification totals as a dashboard chart. */
export class DesignRulesChart implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() modelYear: string | null = null;
  @Input() programName: string | null = null;
  @Input() selectedCpsc: string | null = null;
  @Input() view: 'evidences' | 'classification' = 'evidences';
  @Input() selectedPmt: string | null = null;

  evidencesChartData: any = null;
  evidencesChartOptions: any = null;
  evidencesMetrics: MetricCardData[] = [];
  evidencesLegend: { label: string; color: string; pct: string }[] = [];
  evidencesTotal = 0;
  isLoadingEvidences = false;

  classificationChartData: any = null;
  classificationChartOptions: any = null;
  classificationMetrics: MetricCardData[] = [];
  classificationLegend: { label: string; color: string; pct: string }[] = [];
  classificationTotal = 0;
  isLoadingClassification = false;

  constructor(private vehicleLineService: VehicleLineService) {
    this.registerChartPlugin();
  }

  private registerChartPlugin() {
    const plugin = { id: 'textCenter' };
    Chart.register(plugin);
  }

  ngOnChanges(changes: SimpleChanges) {
    const inputChanged = changes['giCode'] || changes['modelYear'] || changes['programName'] || changes['selectedCpsc'] || changes['view'] || changes['selectedPmt'];
    if (!inputChanged) return;

    if (this.view === 'evidences') {
      if (this.giCode) {
        this.loadEvidencesData();
      } else {
        this.evidencesChartData = null;
        this.evidencesMetrics = [];
      }
    } else {
      if (this.modelYear && this.programName) {
        this.loadClassificationData();
      } else {
        this.classificationChartData = null;
        this.classificationMetrics = [];
      }
    }
  }

  private loadEvidencesData() {
    this.isLoadingEvidences = true;
    this.evidencesChartData = null;

    this.vehicleLineService.getDrEvidencesByAssessment(this.giCode!, this.selectedCpsc, this.selectedPmt).subscribe({
      next: (res) => {
        const items: any[] = res?.data ?? [];

        const totalMeet = items.reduce((a: number, d: any) => a + (d.meet ?? 0), 0);
        const totalDnm  = items.reduce((a: number, d: any) => a + (d.does_not_meet ?? 0), 0);
        const totalUnassessed = items.reduce((a: number, d: any) => a + (d.unassessed ?? 0), 0);

        const labels = ['Meet', 'Does Not Meet', 'Unassessed'];
        const values = [totalMeet, totalDnm, totalUnassessed];
        const colors = ['#00B050', '#FF0000', '#FFC000'];
        this.evidencesTotal = totalMeet + totalDnm + totalUnassessed;

        this.evidencesChartData = {
          labels,
          datasets: [
            {
              label: 'Evidences',
              data: values,
              backgroundColor: colors,
              borderRadius: 6,
              borderSkipped: false,
              barPercentage: 0.5,
              categoryPercentage: 0.6
            }
          ]
        };

        this.evidencesMetrics = [
          { label: 'Meet',          value: totalMeet,      color: 'meet' },
          { label: 'Does Not Meet', value: totalDnm,       color: 'does-not-meet' },
          { label: 'Unassessed',    value: totalUnassessed, color: 'unassessed' }
        ];

        this.evidencesLegend = [
          { label: 'Meet',          color: '#00B050', pct: this.evidencesTotal ? ((totalMeet / this.evidencesTotal) * 100).toFixed(1) : '0' },
          { label: 'Does Not Meet', color: '#FF0000', pct: this.evidencesTotal ? ((totalDnm / this.evidencesTotal) * 100).toFixed(1) : '0' },
          { label: 'Unassessed',    color: '#FFC000', pct: this.evidencesTotal ? ((totalUnassessed / this.evidencesTotal) * 100).toFixed(1) : '0' }
        ];

        this.evidencesChartOptions = this.getSingleBarChartOptions();
        this.isLoadingEvidences = false;
      },
      error: () => {
        this.evidencesChartData = null;
        this.isLoadingEvidences = false;
      }
    });
  }

  private loadClassificationData() {
    this.isLoadingClassification = true;
    this.classificationChartData = null;

    this.vehicleLineService.getDrClassification(this.modelYear!, this.programName!, this.selectedPmt).subscribe({
      next: (res) => {
        const items: any[] = res?.data ?? [];

        // Aggregate totals across all rows (each row = one program/year combination)
        const totals = items.reduce(
          (acc: any, row: any) => ({
            applicable:     acc.applicable     + (row.applicable     ?? 0),
            carryover:      acc.carryover      + (row.carryover      ?? 0),
            not_applicable: acc.not_applicable + (row.not_applicable ?? 0),
            unclassified:   acc.unclassified   + (row.unclassified   ?? 0),
          }),
          { applicable: 0, carryover: 0, not_applicable: 0, unclassified: 0 }
        );

        const labels = ['Applicable', 'Carryover', 'Not Applicable', 'Unclassified'];
        const values = [totals.applicable, totals.carryover, totals.not_applicable, totals.unclassified];
        const colors = ['#00BFA5', '#2196F3', '#FF9800', '#455A64'];
        const colorTokens = ['dr-applicable', 'dr-carryover', 'dr-not-applicable', 'dr-unclassified'];

        this.classificationTotal = values.reduce((a, b) => a + b, 0);

        this.classificationChartData = {
          labels,
          datasets: [{
            label: 'Values',
            data: values,
            backgroundColor: colors,
            borderRadius: 6,
            borderSkipped: false,
            barPercentage: 0.8,
            categoryPercentage: 0.85
          }]
        };

        this.classificationMetrics = labels.map((label, i) => ({
          label,
          value: values[i],
          color: colorTokens[i]
        }));

        this.classificationLegend = labels.map((label, i) => ({
          label,
          color: colors[i],
          pct: this.classificationTotal ? ((values[i] / this.classificationTotal) * 100).toFixed(1) : '0'
        }));

        this.classificationChartOptions = this.getSingleBarChartOptions();
        this.isLoadingClassification = false;
      },
      error: () => {
        this.classificationChartData = null;
        this.isLoadingClassification = false;
      }
    });
  }

  private getSingleBarChartOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: true,
          backgroundColor: 'rgba(38, 50, 56, 0.95)',
          titleColor: '#ffffff',
          bodyColor: '#E0E0E0',
          borderColor: '#546E7A',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 6,
          displayColors: false,
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 12 },
          callbacks: {
            title: (context: any) => context[0].label,
            label: (context: any) => 'Value: ' + context.parsed.y
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#263238', font: { size: 13, weight: '600' }, padding: 10 },
          grid: { display: false, drawBorder: false }
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#546E7A', font: { size: 11, weight: '500' }, padding: 10 },
          grid: { display: true, drawBorder: false, color: 'rgba(236, 239, 241, 0.5)', lineWidth: 1 }
        }
      }
    };
  }
}

```

## `front/dandr-web/src/app/dashboard/components/hir-metrics/hir-metrics.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/hir-metrics/hir-metrics.ts)

```ts
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FedeStatusService } from '../../../services/fede-status.service';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';

@Component({
  selector: 'app-hir-metrics',
  standalone: true,
  imports: [DonutMetricsChartComponent],
  template: `
    <app-donut-metrics-chart
      [isLoading]="isLoading"
      [hasData]="hasData"
      [chartData]="chartData"
      [chartOptions]="chartOptions"
      [total]="totalAssessments"
      totalLabel="Total"
      [legendItems]="legendItems"
      [metricsData]="metricsData"
      [emptyMessage]="emptyMessage"
      [chartSize]="260">
    </app-donut-metrics-chart>
  `,
  styleUrl: './hir-metrics.scss'
})
/** Display live HIR completion metrics for the current filters. */
export class HirMetricsComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() selectedProgram: string | null = null;
  @Input() selectedDvpTeam: string | null = null;
  @Input() selectedPmt: string | null = null;

  hasData = false;
  chartData: any;
  chartOptions: any;
  isLoading = false;
  emptyMessage = 'No data available';
  metricsData: MetricCardData[] = [];
  legendItems: DonutLegendItem[] = [];

  withEvidence = 0;
  withoutEvidence = 0;
  totalAssessments = 0;
  completionPercentage = 0;

  private readonly COLORS = ['#00B050', '#FF5252'];
  private readonly LABELS = ['With Evidence', 'Without Evidence'];

  constructor(private fedeStatusService: FedeStatusService) {
    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: { enabled: true } }
    };
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.giCode) return;
    if (changes['giCode'] || changes['selectedProgram'] || changes['selectedDvpTeam'] || changes['selectedPmt']) {
      this.loadData();
    }
  }

  loadData() {
    if (!this.giCode) return;
    this.isLoading = true;
    this.hasData = false;

    // Set specific empty message based on selection
    if (this.selectedProgram && this.selectedDvpTeam) {
      this.emptyMessage = `No HIR data available for: ${this.selectedProgram} - ${this.selectedDvpTeam}`;
    } else if (this.selectedProgram) {
      this.emptyMessage = `No HIR data available for: ${this.selectedProgram}`;
    } else if (this.selectedDvpTeam) {
      this.emptyMessage = `No HIR data available for DVP Team: ${this.selectedDvpTeam}`;
    } else {
      this.emptyMessage = 'No HIR data available';
    }

    this.fedeStatusService.getHirCompletion(
      this.giCode,
      this.selectedProgram || null,
      this.selectedPmt,
      null,
      this.selectedDvpTeam || null
    ).subscribe({
      next: (response) => {
        if (!response.data || response.data.length === 0 || response.total_records === 0) {
          this.resetChart();
          this.isLoading = false;
          return;
        }

        // Aggregate data from all records
        const aggregated = response.data.reduce(
          (acc, item) => ({
            with_evidence: acc.with_evidence + item.with_evidence,
            without_evidence: acc.without_evidence + item.without_evidence,
            total_items: acc.total_items + item.total_items
          }),
          { with_evidence: 0, without_evidence: 0, total_items: 0 }
        );

        this.withEvidence = aggregated.with_evidence;
        this.withoutEvidence = aggregated.without_evidence;
        this.totalAssessments = aggregated.total_items;
        this.completionPercentage = this.totalAssessments > 0
          ? (this.withEvidence / this.totalAssessments) * 100
          : 0;

        this.buildData();
        this.hasData = true;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error loading HIR completion data:', err);
        this.resetChart();
        this.emptyMessage = 'Error loading HIR data. Please try again.';
        this.isLoading = false;
      }
    });
  }

  resetChart() {
    this.hasData = false;
    this.withEvidence = 0;
    this.withoutEvidence = 0;
    this.totalAssessments = 0;
    this.completionPercentage = 0;
    this.metricsData = [];
    this.legendItems = [];
    this.chartData = null;
  }

  buildData() {
    const values = [this.withEvidence, this.withoutEvidence];
    const pct = (value: number) => this.totalAssessments > 0
      ? ((value / this.totalAssessments) * 100).toFixed(1)
      : '0.0';

    this.metricsData = [
      {
        label: 'Total Items',
        value: this.totalAssessments,
        color: 'total'
      },
      {
        label: 'With Evidence',
        value: this.withEvidence,
        percent: parseFloat(pct(this.withEvidence)),
        color: 'meet'
      },
      {
        label: 'Without Evidence',
        value: this.withoutEvidence,
        percent: parseFloat(pct(this.withoutEvidence)),
        color: 'does-not-meet'
      },
      {
        label: 'Completion %',
        value: Math.round(this.completionPercentage),
        color: 'completion'
      }
    ];

    this.legendItems = this.LABELS.map((label, i) => ({
      label,
      value: values[i],
      pct: pct(values[i]),
      color: this.COLORS[i]
    })).filter(item => item.value > 0);

    this.chartData = {
      labels: this.LABELS,
      datasets: [{
        data: values,
        backgroundColor: this.COLORS,
        borderColor: '#FFFFFF',
        borderWidth: 2,
      }]
    };
  }
}

```

## `front/dandr-web/src/app/dashboard/components/dpa5-metrics/dpa5-metrics.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/dpa5-metrics/dpa5-metrics.ts)

```ts
import { Component, Input, OnInit, OnChanges, SimpleChanges, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgApexchartsModule } from 'ng-apexcharts';
import type {
  ApexAxisChartSeries,
  ApexChart,
  ApexXAxis,
  ApexYAxis,
  ApexPlotOptions,
  ApexLegend,
  ApexTooltip,
  ApexAnnotations,
  ApexDataLabels,
  ApexStroke,
  ApexFill
} from 'ng-apexcharts';
import { LoadingSpinnerComponent } from '../../../shared/components/loading-spinner/loading-spinner';
import { DonutMetricsChartComponent, DonutLegendItem } from '../../../shared/components/donut-metrics-chart';
import { MetricCardData } from '../../../shared/components/metrics-chart-module';
import { Dpa5Service, Dpa5GlidepathPoint } from '../../../services/dpa5.service';

interface Dpa5GlidepathData {
  date: string;
  milestoneName: string | null;
  compliant: number;
  notCompliant: number;
  notAssessable: number;
  assessmentGoal: number | null;
  complianceGoal: number | null;
  compliancePrediction: number | null;
}

interface Dpa5Metrics {
  compliant: number;
  notCompliant: number;
  notAssessable: number;
  total: number;
  complianceRate: number;
}

@Component({
  selector: 'app-dpa5-metrics',
  standalone: true,
  imports: [CommonModule, NgApexchartsModule, LoadingSpinnerComponent, DonutMetricsChartComponent],
  templateUrl: './dpa5-metrics.html',
  styleUrl: './dpa5-metrics.scss',
})
/** Display DPA5 summary metrics and milestone glidepath targets. */
export class Dpa5MetricsComponent implements OnInit, OnChanges, OnDestroy {
  @Input() giCode: string | null = null;
  @Input() selectedProgram: string | null = null;
  @Input() selectedPmt: string | null = null;
  @Input() selectedCpsc: string | null = null;
  @Input() snapshotDate: string | null = null;

  // Donut chart properties
  isLoadingDonut = false;
  hasDonutData = false;
  donutChartData: any;
  donutChartOptions: any;
  donutMetricsData: MetricCardData[] = [];
  donutLegendItems: DonutLegendItem[] = [];
  totalItems = 0;

  private readonly DONUT_COLORS = ['#28a745', '#dc3545', '#007bff'];
  private readonly DONUT_LABELS = ['Compliant', 'Not Compliant', 'Not Assessable'];

  // Chart state
  hasChartData = false;

  // Loading states
  isLoadingGlidepath = false;

  // Error
  errorMessage: string | null = null;

  // ApexCharts properties
  apexSeries: ApexAxisChartSeries = [];
  apexChart: ApexChart = {
    type: 'bar',
    height: 420,
    stacked: true,
    toolbar: { show: true },
    zoom: { enabled: false },
    animations: { enabled: true }
  };
  apexXAxis: ApexXAxis = { categories: [] };
  apexYAxis: ApexYAxis = {
    min: 0,
    max: 100,
    labels: {
      formatter: (val: number) => `${val}%`,
      style: { colors: '#6c757d', fontSize: '12px' }
    },
    title: {
      text: 'Percentage (%)',
      style: { color: '#495057', fontWeight: '600', fontSize: '13px' }
    }
  };
  apexColors: string[] = ['#28a745', '#dc3545', '#007bff', '#6c757d', '#17a2b8', '#ffc107'];
  apexStroke: ApexStroke = {
    width: [0, 0, 0, 2.5, 2.5, 2.5],
    curve: 'smooth',
    dashArray: [0, 0, 0, 0, 0, 6]
  };
  apexPlotOptions: ApexPlotOptions = {
    bar: { columnWidth: '70%' }
  };
  apexDataLabels: ApexDataLabels = { enabled: false };
  apexLegend: ApexLegend = { show: false };
  apexTooltip: ApexTooltip = {
    shared: true,
    intersect: false,
    y: { formatter: (val: number) => val != null ? `${val.toFixed(1)}%` : 'N/A' }
  };
  apexFill: ApexFill = { opacity: [1, 1, 1, 1, 1, 1] };
  apexAnnotations: ApexAnnotations = {};

  // Current metrics for display
  currentMetrics: Dpa5Metrics = {
    compliant: 0,
    notCompliant: 0,
    notAssessable: 0,
    total: 0,
    complianceRate: 0
  };

  constructor(private dpa5Service: Dpa5Service) {
    this.donutChartOptions = {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '72%',
      plugins: { legend: { display: false }, tooltip: { enabled: true } }
    };
  }

  ngOnInit(): void {
    if (this.giCode && this.selectedPmt) {
      this.loadDonutData();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['giCode'] || changes['selectedPmt'] || changes['selectedCpsc'] || changes['snapshotDate']) && this.giCode && this.selectedPmt) {
      this.loadDonutData();
    }
    if (changes['selectedPmt'] && !this.selectedPmt) {
      this.resetData();
    }
  }

  ngOnDestroy(): void {
    // ApexCharts cleanup is handled by NgApexchartsModule automatically
  }

  /**
   * Load all DPA5 data (donut + glidepath) from the real API.
   */
  private loadDonutData(): void {
    if (!this.giCode) return;
    this.isLoadingDonut = true;
    this.isLoadingGlidepath = true;
    this.errorMessage = null;

    this.dpa5Service.getSummary(this.giCode, this.selectedCpsc ?? undefined, this.selectedPmt ?? undefined, this.snapshotDate ?? undefined).subscribe({
      next: (resp) => {
        const { summary, glidepath } = resp;

        // --- Donut ---
        const compliant     = summary.compliant;
        const notCompliant  = summary.not_compliant;
        const notAssessable = summary.not_assessable;
        this.totalItems = summary.total;

        const values = [compliant, notCompliant, notAssessable];

        this.donutMetricsData = [
          { label: 'Total Items', value: this.totalItems },
          ...this.DONUT_LABELS.map((label, i) => ({
            label,
            value: values[i],
            percent: this.totalItems ? Math.round((values[i] / this.totalItems) * 100) : 0,
            color: ['compliant', 'not-compliant', 'not-assessable'][i]
          }))
        ];

        this.donutLegendItems = this.DONUT_LABELS.map((label, i) => ({
          label,
          value: values[i],
          pct: this.totalItems ? ((values[i] / this.totalItems) * 100).toFixed(1) : '0',
          color: this.DONUT_COLORS[i]
        }));

        this.donutChartData = {
          labels: this.DONUT_LABELS,
          datasets: [{
            data: values,
            backgroundColor: this.DONUT_COLORS,
            borderColor: '#FFFFFF',
            borderWidth: 2,
          }]
        };

        this.hasDonutData = true;
        this.isLoadingDonut = false;

        // --- Glidepath ---
        if (!glidepath || glidepath.length === 0) {
          this.hasChartData = false;
          this.isLoadingGlidepath = false;
          return;
        }

        const chartData: Dpa5GlidepathData[] = glidepath.map((p: Dpa5GlidepathPoint) => ({
          date:                p.milestone_date,
          milestoneName:       p.milestone_name ?? null,
          compliant:           p.compliant,
          notCompliant:        p.not_compliant,
          notAssessable:       p.not_assessable,
          assessmentGoal:      p.assessment_goal_curve,
          complianceGoal:      p.compliance_goal_curve,
          compliancePrediction: p.compliance_prediction,
        }));

        this.processGlidepathData(chartData);
        this.isLoadingGlidepath = false;
      },
      error: (err) => {
        console.error('[DPA5 METRICS] Error loading data:', err);
        this.errorMessage = err.error?.detail || 'Error loading DPA5 data';
        this.isLoadingDonut = false;
        this.isLoadingGlidepath = false;
        this.hasDonutData = false;
        this.hasChartData = false;
      }
    });
  }

  /**
   * Public method called from HTML "Try Again" button.
   */
  loadGlidepathData(): void {
    this.loadDonutData();
  }

  private resetData(): void {
    this.hasDonutData = false;
    this.hasChartData = false;
    this.errorMessage = null;
    this.isLoadingDonut = false;
    this.isLoadingGlidepath = false;
    this.totalItems = 0;
    this.donutChartData = null;
    this.donutMetricsData = [];
    this.donutLegendItems = [];
    this.apexSeries = [];
    this.currentMetrics = { compliant: 0, notCompliant: 0, notAssessable: 0, total: 0, complianceRate: 0 };
  }

  private processGlidepathData(data: Dpa5GlidepathData[]): void {
    if (data.length === 0) {
      this.hasChartData = false;
      return;
    }

    const latest = data[data.length - 1];
    this.currentMetrics = {
      compliant: latest.compliant,
      notCompliant: latest.notCompliant,
      notAssessable: latest.notAssessable,
      total: latest.compliant + latest.notCompliant + latest.notAssessable,
      complianceRate: (latest.compliant + latest.notCompliant) > 0
        ? Math.round((latest.compliant / (latest.compliant + latest.notCompliant)) * 100)
        : 0
    };

    this.hasChartData = true;
    try {
      this.renderChart(data);
    } catch (error) {
      console.error('[DPA5 METRICS] Error rendering chart:', error);
      this.errorMessage = 'Failed to render chart';
      this.hasChartData = false;
    }
  }

  /**
   * Render chart with ApexCharts
   */
  private renderChart(chartData: Dpa5GlidepathData[]): void {
    console.log('[DPA5 METRICS] Rendering chart with ApexCharts...');
    console.log('[DPA5 METRICS] chartData length:', chartData.length);

    // Prepare labels — try YYYY-MM-DD parse, fall back to raw string
    const labels = chartData.map(item => {
      const isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(item.date);
      if (isoMatch) {
        const date = new Date(+isoMatch[1], +isoMatch[2] - 1, +isoMatch[3]);
        return date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
      }
      return item.date; // milestone name like "UPV1 09-Jan-2026"
    });

    const safe = (v: number | null | undefined, total: number) =>
      (v != null && total > 0) ? parseFloat(((v / total) * 100).toFixed(1)) : null;

    const computed = chartData.map(item => {
      const total = item.compliant + item.notCompliant + item.notAssessable;
      return {
        compliantPct:          safe(item.compliant, total),
        notCompliantPct:       safe(item.notCompliant, total),
        notAssessablePct:      safe(item.notAssessable, total),
        assessmentGoalPct:     item.assessmentGoal != null ? item.assessmentGoal : null,
        complianceGoalPct:     item.complianceGoal != null ? item.complianceGoal : null,
        compliancePredictionPct: item.compliancePrediction != null ? item.compliancePrediction : null
      };
    });

    // Update series (triggers ApexCharts re-render via Angular binding)
    this.apexSeries = [
      {
        name: 'Compliant',
        type: 'bar',
        data: computed.map(d => d.compliantPct)
      },
      {
        name: 'Not Compliant',
        type: 'bar',
        data: computed.map(d => d.notCompliantPct)
      },
      {
        name: 'Not Assessable',
        type: 'bar',
        data: computed.map(d => d.notAssessablePct)
      },
      {
        name: 'Assessment Goal',
        type: 'line',
        data: computed.map(d => d.assessmentGoalPct)
      },
      {
        name: 'Compliance Goal',
        type: 'line',
        data: computed.map(d => d.complianceGoalPct)
      },
      {
        name: 'Compliance Prediction',
        type: 'line',
        data: computed.map(d => d.compliancePredictionPct)
      }
    ];

    // Update X axis categories
    this.apexXAxis = {
      categories: labels,
      tickAmount: 10,
      labels: {
        rotate: -45,
        rotateAlways: true,
        style: { fontSize: '10px', colors: '#6c757d' },
        hideOverlappingLabels: true
      },
      title: {
        text: 'Date',
        style: { color: '#495057', fontWeight: '600', fontSize: '13px' }
      },
      axisBorder: { show: true, color: '#dee2e6' },
      axisTicks: { show: true }
    };

    // Build milestone vertical annotations using milestoneName from backend.
    // Each data point has a milestoneName (e.g. "UPV1 09-Jan-2026") — we annotate
    // the FIRST occurrence of each unique milestone type (UPV0, UPV1, FDJ, SOP, etc.)
    const annotatedTypes = new Set<string>();
    const xAnnotations = chartData
      .map((item, i) => {
        const name = item.milestoneName;
        if (!name) return null;
        // Extract short milestone type (e.g. "UPV1" from "UPV1 09-Jan-2026")
        const shortType = name.split(' ')[0];
        if (annotatedTypes.has(shortType)) return null;
        annotatedTypes.add(shortType);
        return { label: shortType, category: labels[i] };
      })
      .filter((x): x is { label: string; category: string } => x !== null);

    this.apexAnnotations = {
      xaxis: xAnnotations.map(m => ({
        x: m.category,
        borderColor: '#868e96',
        borderWidth: 2,
        strokeDashArray: 5,
        label: {
          text: m.label,
          borderColor: '#495057',
          style: {
            color: '#fff',
            background: '#495057',
            fontSize: '11px',
            fontWeight: '600',
            padding: { left: 6, right: 6, top: 3, bottom: 3 }
          },
          orientation: 'vertical',
          position: 'top',
          offsetY: 0
        }
      }))
    };

    console.log('[DPA5 METRICS] ApexCharts data set successfully');
  }
}

```

## `front/dandr-web/src/app/dashboard/components/milestone-readiness/milestone-readiness.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/milestone-readiness/milestone-readiness.ts)

```ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { combineLatest, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { MilestoneReadinessService, MilestoneReadinessResponse, MilestoneMetric } from '../../../services/milestone-readiness.service';
import { StateService, ChartType } from '../../../shared/state.service';

@Component({
  selector: 'app-milestone-readiness',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './milestone-readiness.html',
  styleUrls: ['./milestone-readiness.scss'],
})
/** Display cross-deliverable readiness for the selected milestone. */
export class MilestoneReadinessComponent implements OnInit, OnDestroy {
  apiResponse: MilestoneReadinessResponse | null = null;
  activeChart: ChartType = null;
  isLoading = false;
  errorMessage: string | null = null;

  readonly SOURCE_MAP: Record<Exclude<ChartType, null>, string> = {
    cae: 'CAE',
    dvp: 'DVP',
    designRules: 'Design Rules',
    hir: 'HIR',
    costs: 'Costs',
    dpa5: 'DPA5'
  };

  private sub = new Subscription();

  constructor(
    private readinessService: MilestoneReadinessService,
    private state: StateService
  ) {}

  ngOnInit() {
    this.sub.add(
      this.state.activeChart$.subscribe(chart => (this.activeChart = chart))
    );

    this.sub.add(
      combineLatest([this.state.giCode$, this.state.selectedMilestone$, this.state.selectedPmtCode$])
        .pipe(filter(([gi, ms]) => !!gi && !!ms))
        .subscribe(([gi, ms, pmt]) => this.loadReadiness(gi!, ms!, pmt))
    );
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  get currentTarget(): MilestoneMetric | null {
    if (!this.apiResponse?.metrics?.length || !this.activeChart) return null;
    const sourceName = this.SOURCE_MAP[this.activeChart];
    return this.apiResponse.metrics.find(m => m.source === sourceName) ?? null;
  }

  private loadReadiness(giCode: string, milestone: string, pmtCode: string | null) {
    this.isLoading = true;
    this.errorMessage = null;
    this.apiResponse = null;

    this.readinessService.getReadiness(giCode, milestone, pmtCode).subscribe({
      next: (res) => {
        this.apiResponse = res;
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        if (err.status === 404) {
          this.errorMessage = 'Milestone date not defined for this program.';
        } else {
          this.errorMessage = 'Error loading metrics. Please try again later.';
        }
      }
    });
  }
}

```

## `front/dandr-web/src/app/dashboard/components/timeline-milestones/timeline-milestones.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/timeline-milestones/timeline-milestones.ts)

```ts
import { Component, Input, Output, EventEmitter, ViewChild, ElementRef, AfterViewInit, OnChanges, SimpleChanges, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-timeline-milestones',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './timeline-milestones.html',
  styleUrl: './timeline-milestones.scss',
})
/** Render and navigate the chronological vehicle milestone timeline. */
export class TimelineMilestones implements AfterViewInit, OnChanges {

  @Input() milestones: { key: string, value: string }[] = [];
  @Output() milestoneClick = new EventEmitter<{ label: string; date: Date }>();
  @ViewChild('timelineContainer') timelineContainer?: ElementRef;

  private previousMilestonesLength = 0;
  private scrollInterval: any = null;
  private scrollSpeed = 2;

  get formattedMilestones() {
    const formatted = this.milestones
      .map(m => ({
        label: m.key,
        date: new Date(m.value)
      }))
      .sort((a, b) => a.date.getTime() - b.date.getTime());

    // Identify the latest milestone that has already occurred.
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let lastOccurredMilestone: any = null;
    for (let i = formatted.length - 1; i >= 0; i--) {
      const mDate = new Date(formatted[i].date);
      mDate.setHours(0, 0, 0, 0);
      if (mDate.getTime() <= today.getTime()) {
        lastOccurredMilestone = formatted[i];
        break;
      }
    }

    return formatted.map(m => {
      const mDate = new Date(m.date);
      mDate.setHours(0, 0, 0, 0);

      return {
        ...m,
        isActive: lastOccurredMilestone && m.date.getTime() === lastOccurredMilestone.date.getTime(),
        isPast: mDate.getTime() < today.getTime()
      };
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['milestones']) {
      const currentLength = this.milestones.length;
      // Scroll only when the list size changes, indicating a deliverable change.
      if (currentLength !== this.previousMilestonesLength && currentLength > 0) {
        this.previousMilestonesLength = currentLength;
        setTimeout(() => this.scrollToActiveMilestone(), 150);
      }
    }
  }

  ngAfterViewInit() {
    // Center the active milestone on the initial render.
    if (this.formattedMilestones.length > 0 && this.timelineContainer) {
      setTimeout(() => this.scrollToActiveMilestone(), 100);
    }
  }

  private scrollToActiveMilestone() {
    const container = this.timelineContainer?.nativeElement;
    if (!container) return;

    const activeItem = container.querySelector('.timeline-item.is-active');
    if (!activeItem) {
      // Fall back to the latest past milestone when none is active.
      const pastItems = container.querySelectorAll('.timeline-item.is-past');
      if (pastItems.length > 0) {
        const lastPastItem = pastItems[pastItems.length - 1] as HTMLElement;
        this.centerItem(container, lastPastItem);
        return;
      }
      // Center the first item when no milestone has passed.
      const firstItem = container.querySelector('.timeline-item') as HTMLElement;
      if (firstItem) {
        this.centerItem(container, firstItem);
      }
      return;
    }

    this.centerItem(container, activeItem as HTMLElement);
  }

  private centerItem(container: HTMLElement, item: HTMLElement) {
    // Calculate the scroll offset that centers the item.
    const containerWidth = container.offsetWidth;
    const itemLeft = item.offsetLeft;
    const itemWidth = item.offsetWidth;
    const scrollLeft = itemLeft - (containerWidth / 2) + (itemWidth / 2);

    container.scrollTo({
      left: scrollLeft,
      behavior: 'smooth'
    });
  }

  scrollLeft() {
    const container = this.timelineContainer?.nativeElement;
    if (!container) return;
    container.scrollLeft -= 150;
  }

  scrollRight() {
    const container = this.timelineContainer?.nativeElement;
    if (!container) return;
    container.scrollLeft += 150;
  }

  onArrowMouseEnter(direction: 'left' | 'right') {
    this.stopScroll();
    this.scrollInterval = setInterval(() => {
      const container = this.timelineContainer?.nativeElement;
      if (!container) return;

      if (direction === 'left') {
        container.scrollLeft -= this.scrollSpeed;
      } else {
        container.scrollLeft += this.scrollSpeed;
      }
    }, 16); // ~60fps
  }

  onArrowMouseLeave() {
    this.stopScroll();
  }

  private stopScroll() {
    if (this.scrollInterval) {
      clearInterval(this.scrollInterval);
      this.scrollInterval = null;
    }
  }
}

```

## `front/dandr-web/src/app/dashboard/costs-status/costs-status.ts`

[Fonte](../front/dandr-web/src/app/dashboard/costs-status/costs-status.ts)

```ts
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CostsService, CommodityItem, CostDataItem } from '../../services/costs.service';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner';

interface CostTableRow {
  description: string;
  piecePrice: number | string;
  fedebomTarget: number | string;
  gapToTarget: number | string;
  isHighlight?: boolean;
  isSubtotal?: boolean;
  isTotal?: boolean;
  isIndented?: boolean;
  cpsc?: string;
}

interface SummaryData {
  grandTotal: number;
  toolingCost: number;
  pieceCost: number;
  totalRecords: number;
  toolingRecords: number;
  pieceRecords: number;
}

@Component({
  selector: 'app-costs-status',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingSpinnerComponent],
  templateUrl: './costs-status.html',
  styleUrls: ['./costs-status.scss']
})
/** Coordinate the cost summary, filters, and detailed records table. */
export class CostsStatusComponent implements OnChanges {
  @Input() giCode: string | null = null;
  @Input() activeTab: 'pieces' | 'tooling' = 'pieces';
  @Input() selectedPmt: string | null = null;

  isLoading = false;
  isLoadingDropdowns = false;
  isLoadingSummary = false;
  isLoadingCommodities = false;
  isLoadingControlModels = false;
  isLoadingPartNumbers = false;
  errorMessage: string | null = null;

  get activeFilterLabels(): string[] {
    const labels: string[] = [];
    if (this.selectedCommodity) labels.push(`Commodity: ${this.selectedCommodity}`);
    if (this.selectedControlModel) labels.push(`Control Model: ${this.selectedControlModel}`);
    if (this.selectedPartNumber) labels.push(`Part#: ${this.selectedPartNumber}`);
    return labels;
  }

  get filteredTotals(): { actual: number; target: number | string; gap: number } | null {
    const data = this.getCurrentTableData();
    const totalRow = data.find(r => r.isTotal);
    if (!totalRow) return null;
    return {
      actual: typeof totalRow.piecePrice === 'number' ? totalRow.piecePrice : 0,
      target: totalRow.fedebomTarget,
      gap:    typeof totalRow.gapToTarget === 'number' ? totalRow.gapToTarget : 0,
    };
  }
  selectedCommodity: string = '';
  selectedControlModel: string = '';
  selectedPartNumber: string = '';
  availableCommodities: CommodityItem[] = [];
  availableControlModels: string[] = [];
  availablePartNumbers: string[] = [];

  expandedCommodities: Set<string> = new Set();

  tableData: CostTableRow[] = [];

  summaryData: SummaryData = {
    grandTotal: 0,
    toolingCost: 0,
    pieceCost: 0,
    totalRecords: 0,
    toolingRecords: 0,
    pieceRecords: 0
  };

  constructor(private costsService: CostsService) {}

  private loadDropdowns(effectivein: string): void {
    this.isLoadingDropdowns = true;
    this.isLoadingCommodities = true;
    this.isLoadingControlModels = true;
    this.isLoadingPartNumbers = true;
    this.costsService.getDropdownData(effectivein).subscribe({
      next: data => {
        this.availableCommodities = data.commodities;
        this.availableControlModels = data.vehicle_lines;
        this.availablePartNumbers = data.partnumbers;
        this.selectedCommodity = '';
        this.selectedControlModel = '';
        this.selectedPartNumber = '';
        this.isLoadingDropdowns = false;
        this.isLoadingCommodities = false;
        this.isLoadingControlModels = false;
        this.isLoadingPartNumbers = false;
      },
      error: () => {
        this.isLoadingDropdowns = false;
        this.isLoadingCommodities = false;
        this.isLoadingControlModels = false;
        this.isLoadingPartNumbers = false;
      }
    });
  }

  private loadSummary(effectivein: string): void {
    this.isLoadingSummary = true;
    this.costsService.getCombinedMetrics(effectivein, undefined, this.selectedPmt ?? undefined).subscribe({
      next: resp => {
        this.summaryData = {
          grandTotal: resp.summary.grand_total_cost,
          toolingCost: resp.summary.total_tooling_cost,
          pieceCost: resp.summary.total_piece_cost,
          totalRecords: resp.summary.total_tooling_records + resp.summary.total_piece_records,
          toolingRecords: resp.summary.total_tooling_records,
          pieceRecords: resp.summary.total_piece_records
        };
        this.isLoadingSummary = false;
      },
      error: () => { this.isLoadingSummary = false; }
    });
  }

  private loadTableForTab(): void {
    if (!this.giCode) return;
    this.isLoading = true;
    this.errorMessage = null;
    this.tableData = [];
    this.expandedCommodities.clear();

    if (this.activeTab === 'tooling') {
      this.costsService.getToolingMetrics(this.giCode, undefined, this.selectedPmt ?? undefined).subscribe({
        next: resp => {
          this.tableData = this.buildHierarchy(resp.data, 'tooling');
          this.isLoading = false;
        },
        error: () => {
          this.errorMessage = 'Failed to load tooling cost data.';
          this.isLoading = false;
        }
      });
    } else {
      this.costsService.getPieceMetrics(this.giCode, undefined, this.selectedPmt ?? undefined).subscribe({
        next: resp => {
          this.tableData = this.buildHierarchy(resp.data, 'piece');
          this.isLoading = false;
        },
        error: () => {
          this.errorMessage = 'Failed to load piece cost data.';
          this.isLoading = false;
        }
      });
    }
  }

  private buildHierarchy(data: CostDataItem[], type: 'tooling' | 'piece'): CostTableRow[] {
    // Group by cpsc first
    const byCpsc = new Map<string, CostDataItem[]>();
    for (const item of data) {
      const key = item.cpsc ?? 'UNKNOWN';
      if (!byCpsc.has(key)) byCpsc.set(key, []);
      byCpsc.get(key)!.push(item);
    }

    const rows: CostTableRow[] = [];
    let grandActual = 0;
    let grandTarget = 0;
    let grandGap = 0;

    for (const [cpsc, items] of byCpsc) {
      const cpscName = items[0]?.cpsc_name ?? '';

      // Aggregate by partnumber to eliminate duplicates from UNNEST
      const byPn = new Map<string, { actual: number; target: number; gap: number }>();
      for (const item of items) {
        const pn = item.partnumber ?? 'UNKNOWN';
        const actual = type === 'tooling' ? (item.actual_tooling_cost ?? 0) : (item.actual_piece_cost ?? 0);
        const target = type === 'tooling' ? (item.target_tooling_cost ?? 0) : (item.target_piece_cost ?? 0);
        const gap = item.gap ?? 0;
        if (!byPn.has(pn)) {
          byPn.set(pn, { actual, target, gap });
        } else {
          const existing = byPn.get(pn)!;
          existing.actual += actual;
          existing.target += target;
          existing.gap += gap;
        }
      }

      let groupActual = 0;
      let groupTarget = 0;
      let groupGap = 0;
      for (const agg of byPn.values()) {
        groupActual += agg.actual;
        groupTarget += agg.target;
        groupGap += agg.gap;
      }

      grandActual += groupActual;
      grandTarget += groupTarget;
      grandGap += groupGap;

      rows.push({
        description: cpscName ? `${cpsc} - ${cpscName}` : cpsc,
        piecePrice: groupActual,
        fedebomTarget: groupTarget !== 0 ? groupTarget : '-',
        gapToTarget: groupGap,
        isHighlight: true,
        cpsc
      });

      for (const [pn, agg] of byPn) {
        rows.push({
          description: pn,
          piecePrice: agg.actual,
          fedebomTarget: agg.target !== 0 ? agg.target : '-',
          gapToTarget: agg.gap,
          isIndented: true,
          cpsc
        });
      }
    }

    rows.push({
      description: 'Grand Total',
      piecePrice: grandActual,
      fedebomTarget: grandTarget,
      gapToTarget: grandGap,
      isTotal: true
    });

    return rows;
  }

  onPartNumberChange(): void {
    this.expandedCommodities.clear();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['giCode'] && this.giCode) {
      this.loadDropdowns(this.giCode);
      this.loadSummary(this.giCode);
      this.loadTableForTab();
    }
    if (changes['selectedPmt'] && !changes['giCode'] && this.giCode) {
      this.loadSummary(this.giCode);
      this.loadTableForTab();
    }
    if (changes['activeTab'] && !changes['giCode']) {
      this.expandedCommodities.clear();
      this.loadTableForTab();
    }
  }

  getCurrentTableData(): CostTableRow[] {
    let data = this.tableData;

    if (this.selectedCommodity) {
      const filtered: CostTableRow[] = [];
      let insideTarget = false;

      for (const row of data) {
        if (row.isTotal) { filtered.push(row); continue; }

        if (!row.isIndented && row.cpsc === this.selectedCommodity) {
          filtered.push(row);
          insideTarget = true;
          continue;
        }

        if (insideTarget && row.isIndented) {
          filtered.push(row);
        } else if (!row.isIndented) {
          insideTarget = false;
        }
      }

      data = filtered;
    }

    if (this.selectedPartNumber) {
      const filtered: CostTableRow[] = [];
      // Find which commodity parents contain the selected part number
      const parentCpscs = new Set<string>(
        data.filter(r => r.isIndented && r.description === this.selectedPartNumber).map(r => r.cpsc!)
      );

      for (const row of data) {
        if (row.isTotal) { filtered.push(row); continue; }
        // Include parent commodity if it owns the selected part number
        if (!row.isIndented && row.cpsc && parentCpscs.has(row.cpsc)) {
          filtered.push(row);
          continue;
        }
        // Include only the matching child row
        if (row.isIndented && row.description === this.selectedPartNumber) {
          filtered.push(row);
        }
      }

      data = filtered;
    }

    return data;
  }

  isParentRow(row: CostTableRow): boolean {
    if (row.isIndented || row.isTotal || !row.description) return false;
    const idx = this.tableData.indexOf(row);
    if (idx === -1) return false;
    for (let i = idx + 1; i < this.tableData.length; i++) {
      if (this.tableData[i].isTotal) break;
      if (!this.tableData[i].isIndented) break;
      return true;
    }
    return false;
  }

  isExpanded(row: CostTableRow): boolean {
    return this.expandedCommodities.has(row.description);
  }

  toggleCommodityRow(row: CostTableRow): void {
    if (!this.isParentRow(row)) return;
    if (this.expandedCommodities.has(row.description)) {
      this.expandedCommodities.delete(row.description);
    } else {
      this.expandedCommodities.add(row.description);
    }
  }

  getVisibleTableData(): CostTableRow[] {
    const rawData = this.getCurrentTableData();
    const result: CostTableRow[] = [];
    let currentParent = '';

    for (const row of rawData) {
      if (!row.isIndented) {
        currentParent = row.description || '';
        result.push(row);
      } else {
        if (this.expandedCommodities.has(currentParent) || !!this.selectedCommodity) {
          result.push(row);
        }
      }
    }
    return result;
  }

  onCommodityChange(): void {
    this.expandedCommodities.clear();
  }

  onControlModelChange(): void {}

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  }

  formatValue(value: number | string): string {
    if (value === '-' || value === '') return value as string;

    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(numValue)) return '-';

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(numValue);
  }

  getCellColor(value: number | string): string {
    if (value === '-' || value === '') return '#000000';

    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(numValue)) return '#000000';

    if (numValue < 0) return '#FF0000';
    if (numValue > 0) return '#00B050';
    return '#000000';
  }
}

```

## `front/dandr-web/src/app/dashboard/components/extract-button/extract-button.service.ts`

[Fonte](../front/dandr-web/src/app/dashboard/components/extract-button/extract-button.service.ts)

```ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
/** Request export files and trigger browser downloads. */
export class ExtractButtonService {
  constructor(private http: HttpClient) {}

  /**
    * Request a downloadable file from an API endpoint.
    * @param endpointUrl API URL without a query string.
    * @param params Query parameters, such as `{ gi_id: '123' }`.
    * @returns An observable containing the file blob.
   */
  downloadFile(endpointUrl: string, params: Record<string, any>): Observable<Blob> {
    // Build the complete URL from the supplied query parameters.
    const queryString = new URLSearchParams();
    Object.keys(params).forEach(key => {
      queryString.append(key, params[key]);
    });

    const fullUrl = `${endpointUrl}?${queryString.toString()}`;

    return this.http.get(fullUrl, {
      responseType: 'blob'
    });
  }

  /**
    * Trigger a browser download for an in-memory blob.
    * @param blob File content to download.
    * @param fileName File name presented to the user.
   */
  triggerDownload(blob: Blob, fileName: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

```
