import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { VehicleLineService } from '../../../services/vehicle-line.service';
import { FormsModule } from '@angular/forms';

interface CaeData {
  cpsc_code: string;
  assessment_id: string;
  total_unique_dvp_teams: number;
  total_records_for_assessment: number;
  meet: number;
  unassessed: number;
  approved_deviation: number;
  does_not_meet: number;
  cannot_assess: number;
  not_applicable: number;
  dvp_teams?: string[]; // DVP teams associated with this CPSC
}

interface CaeResponse {
  gi_code: string;
  data: CaeData[];
  total_records: number;
}

@Component({
  selector: 'app-cae-status',
  standalone: true,
  imports: [CommonModule, ChartModule, FormsModule],
  template: `
    <div class="cae-status-container">
      <!-- Explanatory header -->
      <div class="cae-header">
        <h3>CAE Status by CPSC Code and DVP Team</h3>
        <p class="cae-description">Data grouped by CPSC Code (e.g., 000600) and DVP Team. Each CPSC code contains multiple DVP Teams with their conformance states.</p>
      </div>

      <!-- Loading Spinner -->
      <div *ngIf="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p class="loading-text">Loading data...</p>
        <p class="loading-subtext">Please wait while we fetch your data</p>
      </div>

      <!-- Content -->
      <div *ngIf="!isLoading && caeChartData" class="cae-content">
        <!-- Assessment Selector -->
        <div class="selectors-row">
          <div class="selector-group" *ngIf="assessments.length > 1">
            <label>Assessment:</label>
            <select [(ngModel)]="selectedAssessment" (change)="onAssessmentChange(selectedAssessment!)">
              <option *ngFor="let assessment of assessments" [value]="assessment">
                {{ assessment }}
              </option>
            </select>
          </div>

          <!-- CPSC Code Selector -->
          <div class="selector-group" *ngIf="cpscCodes.length > 1">
            <label>CPSC Code:</label>
            <select [(ngModel)]="selectedCpscCode" (change)="onCpscCodeChange(selectedCpscCode!)">
              <option *ngFor="let cpsc of cpscCodes" [value]="cpsc">
                {{ cpsc }} ({{ getDvpTeamsForCpsc(cpsc).length }} DVP Teams)
              </option>
            </select>
          </div>

          <!-- DVP Teams Info -->
          <div class="selector-group" *ngIf="currentDvpTeams.length > 0">
            <label>DVP Teams in {{ selectedCpscCode }}:</label>
            <div class="dvp-teams-list">
              <span *ngFor="let team of currentDvpTeams" class="dvp-team-tag">{{ team }}</span>
            </div>
          </div>
        </div>

        <!-- Doughnut Chart -->
        <div class="chart-wrapper">
          <p-chart
            type="doughnut"
            [data]="caeChartData"
            [options]="{
              responsive: true,
              maintainAspectRatio: true,
              plugins: {
                legend: {
                  position: 'bottom',
                  labels: {
                    usePointStyle: true,
                    padding: 15,
                    font: { size: 12, weight: 500 }
                  }
                }
              }
            }"
          ></p-chart>
        </div>
      </div>

      <!-- Empty State -->
      <div *ngIf="!isLoading && !caeChartData" class="empty-state">
        <p>No CAE data available</p>
      </div>
    </div>
  `,
  styleUrl: './cae-status.scss'
})
/** Render CAE assessment status by CPSC and DVP team. */
export class CaeStatusComponent implements OnChanges {
  @Input() giCode: string | null = null;

  caeChartData: any;
  isLoading = false;
  selectedAssessment: string | null = null;
  selectedCpscCode: string | null = null;
  assessments: string[] = [];
  cpscCodes: string[] = [];
  currentDvpTeams: string[] = [];
  rawData: CaeData[] = [];

  constructor(private vehicleLineService: VehicleLineService) {}

  ngOnChanges(changes: SimpleChanges) {
    if (changes['giCode'] && this.giCode) {
      this.loadCaeData();
    }
  }

  loadCaeData() {
    if (!this.giCode) return;

    this.isLoading = true;

    this.vehicleLineService.getCaeGraphData(this.giCode).subscribe({
      next: (response: CaeResponse) => {
        this.rawData = response.data;
        this.assessments = [...new Set(response.data.map(d => d.assessment_id))];
        this.cpscCodes = [...new Set(response.data.map(d => d.cpsc_code))].sort();

        if (this.assessments.length > 0) {
          this.selectedAssessment = this.assessments[0];
        }

        if (this.cpscCodes.length > 0) {
          this.selectedCpscCode = this.cpscCodes[0];
          this.updateDvpTeams();
        }

        this.updateChart();
        this.isLoading = false;
      },
      error: (err: any) => {
        console.error('Failed to load CAE data:', err);
        this.isLoading = false;
      }
    });
  }

  updateChart() {
    if (!this.selectedAssessment) return;

    const filteredData = this.rawData.filter(d => d.assessment_id === this.selectedAssessment);

    if (filteredData.length === 0) {
      this.caeChartData = null;
      return;
    }

    // Aggregate every CPSC represented by the selected assessment.
    const aggregated = {
      meet: filteredData.reduce((sum, d) => sum + d.meet, 0),
      unassessed: filteredData.reduce((sum, d) => sum + d.unassessed, 0),
      approved_deviation: filteredData.reduce((sum, d) => sum + d.approved_deviation, 0),
      does_not_meet: filteredData.reduce((sum, d) => sum + d.does_not_meet, 0),
      cannot_assess: filteredData.reduce((sum, d) => sum + d.cannot_assess, 0),
      not_applicable: filteredData.reduce((sum, d) => sum + d.not_applicable, 0),
    };

    this.caeChartData = {
      labels: ['Meet', 'Unassessed', 'Approved Deviation', 'Does Not Meet', 'Cannot Assess', 'Not Applicable'],
      datasets: [
        {
          data: [
            aggregated.meet,
            aggregated.unassessed,
            aggregated.approved_deviation,
            aggregated.does_not_meet,
            aggregated.cannot_assess,
            aggregated.not_applicable,
          ],
          backgroundColor: [
            '#00B050', // Green - Meet
            '#FFC000', // Yellow - Unassessed
            '#FF9900', // Orange - Approved Deviation
            '#FF0000', // Red - Does Not Meet
            '#808080', // Gray - Cannot Assess
            '#CCCCCC', // Light Gray - Not Applicable
          ],
          borderColor: '#FFFFFF',
          borderWidth: 2,
        }
      ]
    };
  }

  onAssessmentChange(assessment: string) {
    this.selectedAssessment = assessment;
    this.updateChart();
  }

  onCpscCodeChange(cpscCode: string) {
    this.selectedCpscCode = cpscCode;
    this.updateDvpTeams();
    this.updateChart();
  }

  updateDvpTeams() {
    if (!this.selectedCpscCode) {
      this.currentDvpTeams = [];
      return;
    }

    const cpscData = this.rawData.filter(d => d.cpsc_code === this.selectedCpscCode);
    // Estima DVP Teams baseado na contagem de dvp_teams
    this.currentDvpTeams = cpscData.map((_, i) => `DVP Team ${i + 1} (${cpscData[i]?.total_unique_dvp_teams || 0} teams)`);
  }

  getDvpTeamsForCpsc(cpscCode: string): string[] {
    const cpscData = this.rawData.filter(d => d.cpsc_code === cpscCode);
    return cpscData.map((_, i) => `DVP Team ${i + 1}`);
  }
}
