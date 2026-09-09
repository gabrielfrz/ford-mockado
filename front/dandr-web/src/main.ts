import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { MessageService } from 'primeng/api';
import { App } from './app/app';
import { routes } from './app/app.routes';
bootstrapApplication(App, { providers: [provideRouter(routes), provideHttpClient(), MessageService] }).catch(console.error);
