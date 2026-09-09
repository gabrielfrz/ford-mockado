import { Injectable } from '@angular/core';
import { MessageService } from 'primeng/api';

/** Supported notification severity levels. */
export type ToastSeverity = 'success' | 'info' | 'warn' | 'error';

/** Notification content consumed by the global toast component. */
export interface ToastMessage {
  severity: ToastSeverity;
  summary: string;
  detail?: string;
  life?: number;
}

@Injectable({
  providedIn: 'root'
})
/** Publish consistently configured application notifications. */
export class ToastService {
  constructor(private messageService: MessageService) {}

  /** Publish a notification with explicit display settings. */
  show(message: ToastMessage) {
    this.messageService.add({
      severity: message.severity,
      summary: message.summary,
      detail: message.detail || '',
      life: message.life || 4000
    });
  }

  /** Publish a success notification. */
  success(summary: string, detail?: string) {
    this.show({
      severity: 'success',
      summary,
      detail,
      life: 5000
    });
  }

  /** Publish an error notification. */
  error(summary: string, detail?: string) {
    this.show({
      severity: 'error',
      summary,
      detail,
      life: 6000
    });
  }

  /** Publish an informational notification. */
  info(summary: string, detail?: string) {
    this.show({
      severity: 'info',
      summary,
      detail,
      life: 4000
    });
  }

  /** Publish a persistent loading notification. */
  loading(summary: string, detail?: string) {
    this.show({
      severity: 'info',
      summary,
      detail,
      life: 999999
    });
  }

  /** Publish a warning notification. */
  warning(summary: string, detail?: string) {
    this.show({
      severity: 'warn',
      summary,
      detail,
      life: 5000
    });
  }

  /** Remove all active notifications. */
  clear() {
    this.messageService.clear();
  }
}
