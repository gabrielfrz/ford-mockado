import { Routes } from '@angular/router';
import { Home } from './dashboard/home/home';
import { FedeStatus } from './dashboard/fede-status/fede-status';

/** Application routes used by the Angular router. */
export const routes: Routes = [
  { path: '', component: Home, title: 'Engineering Dashboard' },
  {
    path: 'fede-status',
    component: FedeStatus,
    title: 'FEDE Status',
  },
  { path: '**', redirectTo: '' },
];
