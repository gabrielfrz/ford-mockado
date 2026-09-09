import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { FedeStatusService } from '../../../services/fede-status.service';
import { LoadingSpinnerComponent } from '../../../shared/components/loading-spinner';

// Color map for all possible conf_state values
const CONF_STATE_COLOR_MAP: { [key: string]: string } = {
  'Meet': '#4CAF50',                    // Green
  'Unassessed': '#F44336',              // Red
  'Does Not Meet': '#2196F3',           // Blue
  'Cannot Assess': '#9C27B0',           // Purple
  'Not Applicable': '#607D8B',          // Slate Gray
  'Approved Deviation': '#FFEB3B'       // Yellow
};

@Component({
  selector: 'app-dvp-status',
  standalone: true,
  imports: [CommonModule, ChartModule, LoadingSpinnerComponent],
  templateUrl: './dvp-status.html',
  styleUrl: './dvp-status.scss',
})
/** Coordinate DVP team and CPSC status visualizations. */
export class DvpStatus implements OnInit, OnChanges {
  @Input() summaryData: any = null;
  @Input() giCode: string | null = null;
  @Input() set selectedDvpTeam(value: string | null) {
    this._selectedDvpTeam = value;
    // Reload the CPSC chart when the selected DVP team changes.
    if (value && this.giCode) {
      this.loadCpscBreakdown(this.giCode);
    }
  }
  get selectedDvpTeam(): string | null {
    return this._selectedDvpTeam;
  }
  private _selectedDvpTeam: string | null = null;

  // Assessment chart (doughnut)
  assessmentChartData: any = null;
  assessmentChartOptions: any = null;
  assessmentLoading = false;
  assessmentError: string | null = null;

  // Classification chart (doughnut)
  classificationChartData: any = null;
  classificationChartOptions: any = null;
  classificationLoading = true;

  // CPSC breakdown chart (doughnut - filtered by DVP Team)
  cpscChartData: any = null;
  cpscChartOptions: any = null;
  cpscLoading = false;
  cpscError: string | null = null;

  constructor(private fedeService: FedeStatusService) {}

  ngOnInit() {}

  ngOnChanges(changes: SimpleChanges) {
    // Load assessment data when giCode changes
    if (changes['giCode'] && changes['giCode'].currentValue) {
      this.loadAssessmentStatus(changes['giCode'].currentValue);
      this.loadCpscBreakdown(changes['giCode'].currentValue);
      this.initClassificationChart();
    }
  }

  private loadAssessmentStatus(giCode: string) {
    this.assessmentLoading = true;
    this.assessmentError = null;

    console.log('[ASSESSMENT] Loading assessment status for giCode:', giCode);

    this.fedeService.getConfStateMetrics(giCode).subscribe({
      next: (response: any) => {
        console.log('[ASSESSMENT] Data loaded:', response);
        this.assessmentLoading = false;
        this.initAssessmentChartFromData(response);
      },
      error: (err: any) => {
        console.error('[ASSESSMENT] Error loading assessment status:', err);

        if (err.status === 404) {
          this.assessmentError = 'Assessment Status endpoint not implemented';
        } else {
          this.assessmentError = `Failed to load Assessment Status: ${err.status} ${err.statusText || err.message}`;
        }
        this.assessmentLoading = false;
      }
    });
  }

  private initAssessmentChartFromData(data: any) {
    const confStateSummary = data.conf_state_summary || {};

    const labels: string[] = [];
    const dataValues: number[] = [];
    const backgroundColors: string[] = [];

    // Render all states from backend in descending order by count
    const sortedStates = Object.entries(confStateSummary)
      .sort(([, a], [, b]) => (b as number) - (a as number));

    sortedStates.forEach(([state, count]) => {
      labels.push(state);
      dataValues.push(count as number);
      // Use color from map or default gray if not found
      backgroundColors.push(CONF_STATE_COLOR_MAP[state] || '#999999');
    });

    this.assessmentChartData = {
      labels,
      datasets: [
        {
          data: dataValues,
          backgroundColor: backgroundColors,
          hoverBackgroundColor: backgroundColors.map(c => this.darkenColor(c)),
          borderColor: '#ffffff',
          borderWidth: 2
        }
      ]
    };

    this.assessmentChartOptions = this.getBarChartOptions(backgroundColors);
    this.assessmentLoading = false;
  }

  private loadCpscBreakdown(giCode: string) {
    this.cpscLoading = true;
    this.cpscError = null;

    console.log('[CPSC] Loading CPSC conf-state breakdown for giCode:', giCode);

    this.fedeService.getCpscConfStateBreakdown(giCode).subscribe({
      next: (response: any) => {
        console.log('[CPSC] Data loaded:', response);
        this.cpscLoading = false;
        this.initCpscChartFromData(response);
      },
      error: (err: any) => {
        console.error('[CPSC] Error loading CPSC breakdown:', err);
        console.log('[CPSC] Using mock data...');
        this.initCpscChartFromMockData();
        this.cpscLoading = false;
      }
    });
  }

  private initCpscChartFromMockData() {
    // Mock data for CPSC breakdown with smaller values
    const mockCpscMetrics = {
      cpsc_metrics: {
        'CPSC-001': {
          name: 'CPSC-001',
          conf_state_breakdown: { 'Meet': 45, 'Does Not Meet': 8, 'Unassessed': 5 }
        },
        'CPSC-002': {
          name: 'CPSC-002',
          conf_state_breakdown: { 'Meet': 38, 'Does Not Meet': 10, 'Unassessed': 3 }
        },
        'CPSC-003': {
          name: 'CPSC-003',
          conf_state_breakdown: { 'Meet': 52, 'Does Not Meet': 6, 'Unassessed': 7 }
        }
      }
    };

    this.initCpscChartFromData(mockCpscMetrics);
  }

  private initCpscChartFromData(data: any) {
    const cpscMetrics = data.cpsc_metrics || {};

    // Aggregate all conf_states across all CPSCs
    const confStateAggregation: { [key: string]: number } = {};
    let total = 0;

    Object.values(cpscMetrics).forEach((metric: any) => {
      if (metric.conf_state_breakdown) {
        Object.entries(metric.conf_state_breakdown).forEach(([state, count]: [string, any]) => {
          confStateAggregation[state] = (confStateAggregation[state] || 0) + count;
          total += count;
        });
      }
    });

    const labels: string[] = [];
    const dataValues: number[] = [];
    const backgroundColors: string[] = [];

    // Render all states in descending order by count
    const sortedStates = Object.entries(confStateAggregation)
      .sort(([, a], [, b]) => (b as number) - (a as number));

    sortedStates.forEach(([state, count]) => {
      labels.push(state);
      dataValues.push(count as number);
      backgroundColors.push(CONF_STATE_COLOR_MAP[state] || '#999999');
    });

    this.cpscChartData = {
      labels,
      datasets: [
        {
          data: dataValues,
          backgroundColor: backgroundColors,
          hoverBackgroundColor: backgroundColors.map(c => this.darkenColor(c)),
          borderColor: '#ffffff',
          borderWidth: 2
        }
      ]
    };

    this.cpscChartOptions = this.getBarChartOptions(backgroundColors);
    this.cpscLoading = false;
  }

  private initClassificationChart() {
    this.classificationLoading = true;
    const classificationValues = { applicable: 280, carryover: 320, notApplicable: 140, unclassified: 40 };
    const labels = ['Applicable', 'Carryover', 'Not Applicable', 'Unclassified'];
    const values = [classificationValues.applicable, classificationValues.carryover, classificationValues.notApplicable, classificationValues.unclassified];
    const colors = ['#00BFA5', '#2196F3', '#FF9800', '#455A64'];

    this.classificationChartData = {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors,
          hoverBackgroundColor: colors.map(c => this.darkenColor(c)),
          borderColor: '#ffffff',
          borderWidth: 2
        }
      ]
    };

    this.classificationChartOptions = this.getBarChartOptions(colors);
    this.classificationLoading = false;
  }

  private getBarChartOptions(colors: string[]) {
    return {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            padding: 20,
            font: {
              size: 13,
              weight: '600'
            }
          }
        },
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
          bodyFont: { size: 12 }
        }
      }
    };
  }

  /**
   * Darkens a hex color for hover effect
   * @param color Hex color string (e.g., '#4CAF50')
   * @returns Darkened hex color
   */
  private darkenColor(color: string): string {
    const hex = color.replace('#', '');
    let r = parseInt(hex.substring(0, 2), 16);
    let g = parseInt(hex.substring(2, 4), 16);
    let b = parseInt(hex.substring(4, 6), 16);

    r = Math.max(0, r - 40);
    g = Math.max(0, g - 40);
    b = Math.max(0, b - 40);

    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }
}



