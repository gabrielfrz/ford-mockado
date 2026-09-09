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
