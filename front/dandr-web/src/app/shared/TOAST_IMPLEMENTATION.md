# Toast Service Documentation

## Overview

The `ToastService` was created to provide visual feedback to the user about the status of backend requests. It integrates PrimeNG Toast to display non-intrusive messages.

## Implementation

### 1. Toast Service (`toast.service.ts`)

A centralized service that manages all application notifications.

**Available methods:**

- `success(summary: string, detail?: string)` - Success message (5s)
- `error(summary: string, detail?: string)` - Error message (6s)
- `info(summary: string, detail?: string)` - Informative message (4s)
- `warning(summary: string, detail?: string)` - Warning message (5s)
- `loading(summary: string, detail?: string)` - Persistent message (does not disappear automatically)
- `clear()` - Clears all notifications

### 2. Global Setup

The Toast was configured in the root component (`app.ts`):

```typescript
// Imports
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

@Component({
  imports: [ToastModule]
})
```

The display component was added in the template (`app.html`):

```html
<p-toast position="top-right" [baseZIndex]="1000" styleClass="custom-toast"></p-toast>
```

And `MessageService` was added as a global provider in `main.ts`:

```typescript
import { provideAnimations } from '@angular/platform-browser/animations';
import { MessageService } from 'primeng/api';

bootstrapApplication(App, {
  providers: [
    provideAnimations(),
    MessageService
  ]
});
```

### 3. Styling

Toast styles are located in a dedicated file: `toast.styles.scss`

The styles include:
- Custom gradients for each severity level
- Smooth animations and transitions
- Professional color scheme
- Responsive font sizing

## Usage in Home Component

### Autocomplete Filters

The component automatically detects when the user is typing in the filter fields:

```typescript
filterModelYears(event: any) {
  this.toastService.info('Loading...', 'Fetching model years');
  this.service.getModelYears(event.query).subscribe({
    next: (resp) => {
      this.filteredModelYears = resp.map(x => ({ label: x, value: x }));
      this.toastService.success('Success!', `${resp.length} year(s) found`);
    },
    error: (err) => {
      console.error(err);
      this.toastService.error('Error', 'Could not load model years');
    }
  });
}
```

### Search Button

The `submitForm()` method now displays toasts for each step:

1. **Validation** - If fields are missing:
   ```
   Required fields
   Please fill all fields
   ```

2. **Loading** - When the request is sent:
   ```
   Processing...
   Fetching summary data
   ```

3. **Success** - When data is returned:
   ```
   Success!
   Data loaded for [Vehicle Line]
   ```

4. **Error** - If the request fails:
   ```
   Search failed
   [backend error message]
   ```

## Usage Examples

### Error handling with backend details

```typescript
error: (err) => {
  const errorMsg = err?.error?.detail || 'Unknown error';
  this.toastService.error('Operation failed', errorMsg);
}
```

### Multiple requests

```typescript
private loadData() {
  this.toastService.info('Starting...', 'Loading data');
  
  this.service.getData().subscribe({
    next: (data) => {
      this.toastService.success('Complete!', 'Data loaded successfully');
    },
    error: (err) => {
      this.toastService.error('Error!', 'Failed to load data');
    }
  });
}
```

## Toast Styling

- **Success**: Green gradient background, white text, 5 seconds
- **Error**: Red gradient background, white text, 6 seconds
- **Info**: Blue gradient background, white text, 4 seconds
- **Warning**: Orange gradient background, white text, 5 seconds

Messages appear in the top-right corner of the screen with smooth slide-in animation.

## File Structure

```
src/app/
├── app.ts (includes ToastModule)
├── app.html (includes p-toast component)
├── app.scss (imports toast.styles.scss)
├── shared/
│   ├── toast.service.ts (service)
│   ├── toast.styles.scss (styles)
│   └── TOAST_IMPLEMENTATION.md (this file)
└── dashboard/home/
    ├── home.ts (uses ToastService)
    └── home.html
```

## Future Improvements

- Add toasts to other components
- Configure persistence for long-running requests
- Create custom toasts with actions
- Internationalization support

