import { Routes } from '@angular/router';
import { Workspace } from './components/workspace/workspace';
import { Dashboard } from './components/dashboard/dashboard';
import { Analytics } from './components/analytics/analytics';
import { Settings } from './components/settings/settings';

export const routes: Routes = [
  { path: 'dashboard', component: Dashboard },
  { path: 'chat', component: Workspace },
  { path: 'analytics', component: Analytics },
  { path: 'settings', component: Settings },
  { path: '', redirectTo: 'chat', pathMatch: 'full' }
];
