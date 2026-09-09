import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CostsService } from '../../../services/costs.service';

interface CostMetrics {
  totalToolingCost: number;
  totalPieceCost: number;
  grandTotalCost: number;
  toolingRecords: number;
  pieceRecords: number;
  cpscBreakdown: { [cpsc: string]: { tooling: number; piece: number; total: number } };
}

@Component({
  selector: 'app-costs-metrics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './costs-metrics.html',
  styleUrls: ['./costs-metrics.scss']
})
/** Display combined tooling- and piece-cost metric cards. */
export class CostsMetricsComponent implements OnChanges {
  @Input() effectivePoint: string | null = null;
  @Input() selectedCpsc: string | null = null;
  @Input() selectedPmtCode: string | null = null;

  isLoading = false;
  hasData = false;
  errorMessage: string | null = null;

  metrics: CostMetrics = {
    totalToolingCost: 0,
    totalPieceCost: 0,
    grandTotalCost: 0,
    toolingRecords: 0,
    pieceRecords: 0,
    cpscBreakdown: {}
  };

  topCpscsByTooling: Array<{ cpsc: string; cost: number; percentage: number }> = [];
  topCpscsByPiece: Array<{ cpsc: string; cost: number; percentage: number }> = [];

  // Chart colors
  private readonly CHART_COLORS = [
    '#00B050', '#FFC000', '#FF9900', '#FF5252', '#9C27B0',
    '#3F51B5', '#00BCD4', '#4CAF50', '#FFEB3B', '#FF9800'
  ];

  constructor(private costsService: CostsService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['effectivePoint'] || changes['selectedCpsc'] || changes['selectedPmtCode']) {
      if (this.effectivePoint) {
        this.loadCostData();
      } else {
        this.resetData();
      }
    }
  }

  private loadCostData(): void {
    if (!this.effectivePoint) return;

    this.isLoading = true;
    this.hasData = false;
    this.errorMessage = null;

    this.costsService.getCombinedMetrics(
      this.effectivePoint,
      this.selectedCpsc || undefined,
      this.selectedPmtCode || undefined
    ).subscribe({
      next: (response) => {
        if (response.summary.total_tooling_records === 0 && response.summary.total_piece_records === 0) {
          this.errorMessage = 'No cost data available for the selected filters';
          this.isLoading = false;
          this.hasData = false;
          return;
        }

        this.metrics = {
          totalToolingCost: response.summary.total_tooling_cost,
          totalPieceCost: response.summary.total_piece_cost,
          grandTotalCost: response.summary.grand_total_cost,
          toolingRecords: response.summary.total_tooling_records,
          pieceRecords: response.summary.total_piece_records,
          cpscBreakdown: {}
        };

        // Calculate CPSC breakdown
        this.calculateCpscBreakdown(response);

        // Calculate top CPSCs
        this.calculateTopCpscs();

        this.hasData = true;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error loading cost data:', err);
        this.errorMessage = err.error?.detail || 'Error loading cost data';
        this.isLoading = false;
        this.hasData = false;
      }
    });
  }

  private calculateCpscBreakdown(response: any): void {
    const breakdown: { [cpsc: string]: { tooling: number; piece: number; total: number } } = {};

    // Process tooling data
    response.tooling_cost.data.forEach((item: any) => {
      if (!breakdown[item.cpsc]) {
        breakdown[item.cpsc] = { tooling: 0, piece: 0, total: 0 };
      }
      breakdown[item.cpsc].tooling += item.actual_tooling_cost || 0;
    });

    // Process piece data
    response.piece_cost.data.forEach((item: any) => {
      if (!breakdown[item.cpsc]) {
        breakdown[item.cpsc] = { tooling: 0, piece: 0, total: 0 };
      }
      breakdown[item.cpsc].piece += item.actual_piece_cost || 0;
    });

    // Calculate totals
    Object.keys(breakdown).forEach(cpsc => {
      breakdown[cpsc].total = breakdown[cpsc].tooling + breakdown[cpsc].piece;
    });

    this.metrics.cpscBreakdown = breakdown;
  }

  private calculateTopCpscs(): void {
    const cpscEntries = Object.entries(this.metrics.cpscBreakdown);

    // Top by tooling
    this.topCpscsByTooling = cpscEntries
      .map(([cpsc, costs]) => ({
        cpsc,
        cost: costs.tooling,
        percentage: this.metrics.totalToolingCost > 0
          ? (costs.tooling / this.metrics.totalToolingCost) * 100
          : 0
      }))
      .filter(item => item.cost > 0)
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 5);

    // Top by piece
    this.topCpscsByPiece = cpscEntries
      .map(([cpsc, costs]) => ({
        cpsc,
        cost: costs.piece,
        percentage: this.metrics.totalPieceCost > 0
          ? (costs.piece / this.metrics.totalPieceCost) * 100
          : 0
      }))
      .filter(item => item.cost > 0)
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 5);
  }

  private resetData(): void {
    this.hasData = false;
    this.errorMessage = null;
    this.metrics = {
      totalToolingCost: 0,
      totalPieceCost: 0,
      grandTotalCost: 0,
      toolingRecords: 0,
      pieceRecords: 0,
      cpscBreakdown: {}
    };
    this.topCpscsByTooling = [];
    this.topCpscsByPiece = [];
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  }

  formatPercentage(value: number): string {
    return `${value.toFixed(1)}%`;
  }

  getColorForIndex(index: number): string {
    return this.CHART_COLORS[index % this.CHART_COLORS.length];
  }
}
