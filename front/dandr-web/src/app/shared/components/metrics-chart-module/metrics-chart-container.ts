import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

/** Label and value used by the chart filter selector. */
export interface SelectOption {
  label: string;
  value: any;
}

/** Metric card content projected into the chart container. */
export interface MetricCard {
  label: string;
  value: string | number;
  percent?: string | number;
  color?: string; // 'meet' | 'unassessed' | 'approved-deviation' | 'does-not-meet' | 'cannot-assess' | 'not-applicable'
}

@Component({
  selector: 'app-metrics-chart-container',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <!-- Header: Title + Selector -->
    <div class="metrics-header">
      <h2 class="metrics-title">{{ title }}</h2>
      <div class="metrics-selector" *ngIf="showSelector && selectOptions.length > 0">
        <label [for]="selectId">{{ selectLabel }}:</label>
        <select
          [id]="selectId"
          [(ngModel)]="selectedValue"
          (change)="onSelectionChange()"
          class="selector"
        >
          <option [value]="null">{{ selectPlaceholder }}</option>
          <option *ngFor="let opt of selectOptions" [value]="opt.value">
            {{ opt.label }}
          </option>
        </select>
      </div>
    </div>

    <!-- Content: Metrics + Chart -->
    <div class="metrics-content">
      <div class="metrics-section">
        <ng-content select="[metrics]"></ng-content>
      </div>

      <div class="chart-section">
        <ng-content select="[chart]"></ng-content>
      </div>
    </div>
  `,
  styleUrls: ['./metrics-chart-container.scss']
})
/** Layout container for a selector, metric cards, and projected chart content. */
export class MetricsChartContainerComponent {
  @Input() title: string = 'Chart Title';
  @Input() showSelector: boolean = true;
  @Input() selectLabel: string = 'Select Option';
  @Input() selectPlaceholder: string = 'Choose...';
  @Input() selectId: string = 'metrics-select';
  @Input() selectOptions: SelectOption[] = [];

  @Output() selectionChanged = new EventEmitter<any>();

  selectedValue: any = null;

  onSelectionChange() {
    this.selectionChanged.emit(this.selectedValue);
  }
}
