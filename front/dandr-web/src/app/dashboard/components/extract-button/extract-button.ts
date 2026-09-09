import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ExtractButtonService } from './extract-button.service';

@Component({
  selector: 'app-extract-button',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button
      class="extract-btn"
      [disabled]="isLoading || !isEnabled"
      (click)="onDownload()"
      [attr.title]="buttonTooltip"
    >
      <!-- Download icon -->
      <svg
        *ngIf="!isLoading"
        class="download-icon"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>

      <!-- Loading spinner -->
      <div *ngIf="isLoading" class="spinner-icon"></div>

      <!-- Texto -->
      <span class="button-text">
        {{ isLoading ? 'Exporting...' : buttonLabel }}
      </span>
    </button>
  `,
  styleUrl: './extract-button.scss',
  providers: [ExtractButtonService]
})
/** Reusable export button with loading and error feedback. */
export class ExtractButtonComponent {
  @Input() endpointUrl: string = '';
  @Input() fileName: string = 'export.csv';
  @Input() params: Record<string, any> = {};
  @Input() buttonLabel: string = 'Exportar';
  @Input() isEnabled: boolean = true;

  isLoading = false;

  get buttonTooltip(): string {
    if (!this.isEnabled) return 'Select data to export';
    return this.isLoading ? 'Exporting...' : `Export as ${this.fileName}`;
  }

  constructor(private extractService: ExtractButtonService) {}

  onDownload(): void {
    if (!this.endpointUrl || !this.params || this.isLoading || !this.isEnabled) {
      console.warn('Invalid request: missing required parameters');
      return;
    }

    this.isLoading = true;

    this.extractService.downloadFile(this.endpointUrl, this.params).subscribe({
      next: (blob: Blob) => {
        this.extractService.triggerDownload(blob, this.fileName);
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error downloading file:', err);
        alert(`Export error: ${err?.error?.message || 'Please try again later'}`);
        this.isLoading = false;
      }
    });
  }
}
