# Metrics Chart Module

Reusable components for building metric charts throughout the application.

## Components

### `MetricsChartContainerComponent`

Main container that organizes:

- Title
- Filter selector
- Metric grid
- Chart section

#### Inputs

| Property            | Type             | Default          | Description                 |
| ------------------- | ---------------- | ---------------- | --------------------------- |
| `title`             | `string`         | 'Chart Title'    | Chart title                 |
| `showSelector`      | `boolean`        | `true`           | Shows or hides the selector |
| `selectLabel`       | `string`         | 'Select Option'  | Selector label              |
| `selectPlaceholder` | `string`         | 'Choose...'      | Selector placeholder        |
| `selectId`          | `string`         | 'metrics-select' | Selector element ID         |
| `selectOptions`     | `SelectOption[]` | `[]`             | Available selector options  |

#### Outputs

| Event              | Value | Description                        |
| ------------------ | ----- | ---------------------------------- |
| `selectionChanged` | `any` | Emitted when the selection changes |

#### Content projection

```html
<app-metrics-chart-container
  title="CAE STATUS"
  [selectOptions]="programOptions"
  (selectionChanged)="onProgramChange($event)"
>
  <!-- Metrics -->
  <app-metrics-grid [metrics]="metricsData" metrics> </app-metrics-grid>

  <!-- Chart -->
  <p-chart type="doughnut" [data]="chartData" chart> </p-chart>
</app-metrics-chart-container>
```

### `MetricsGridComponent`

Responsive grid for displaying metric cards.

#### Inputs

| Property  | Type               | Description        |
| --------- | ------------------ | ------------------ |
| `metrics` | `MetricCardData[]` | Metrics to display |

#### Types

```typescript
interface MetricCardData {
  label: string;
  value: string | number;
  percent?: string | number;
  color?:
    | 'meet'
    | 'unassessed'
    | 'approved-deviation'
    | 'does-not-meet'
    | 'cannot-assess'
    | 'not-applicable'
    | string;
}

interface SelectOption {
  label: string;
  value: any;
}
```

## Complete example

```typescript
import { Component, OnInit } from '@angular/core';
import {
  MetricsChartContainerComponent,
  MetricsGridComponent,
  MetricCardData,
  SelectOption,
} from '@app/shared/components/metrics-chart-module';
import { ChartModule } from 'primeng/chart';

@Component({
  selector: 'app-my-chart',
  standalone: true,
  imports: [MetricsChartContainerComponent, MetricsGridComponent, ChartModule],
  template: `
    <app-metrics-chart-container
      title="MY METRICS"
      selectLabel="Select Program"
      [selectOptions]="programs"
      (selectionChanged)="onProgramChange($event)"
    >
      <app-metrics-grid [metrics]="metrics" metrics> </app-metrics-grid>

      <p-chart type="doughnut" [data]="chartData" chart> </p-chart>
    </app-metrics-chart-container>
  `,
})
export class MyChartComponent implements OnInit {
  programs: SelectOption[] = [];
  metrics: MetricCardData[] = [];
  chartData: any;

  ngOnInit() {
    this.loadPrograms();
    this.loadMetrics();
  }

  loadPrograms() {
    this.programs = [
      { label: 'Program A', value: 'prog_a' },
      { label: 'Program B', value: 'prog_b' },
    ];
  }

  loadMetrics() {
    this.metrics = [
      { label: 'Total', value: 150, color: 'meet' },
      { label: 'Unassessed', value: 45, percent: 30, color: 'unassessed' },
      { label: 'Does Not Meet', value: 10, percent: 6.7, color: 'does-not-meet' },
    ];
  }

  onProgramChange(value: any) {
    console.log('Program changed:', value);
    this.loadMetrics();
  }
}
```

## Styling

The module includes production-ready styling:

- White container with a shadow
- Responsive metric grid
- Standard colors for each metric type
- Fully responsive layout

Consumers only need to provide the data.
