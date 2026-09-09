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
