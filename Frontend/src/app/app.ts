import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Header } from './components/header/header';
import { ToastComponent } from './components/toast/toast';
import { RouterModule } from '@angular/router';

// Angular Material + Forms
import { MatSliderModule } from '@angular/material/slider';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-root',
  imports: [
        FormsModule, 
        Header, 
        ToastComponent,RouterModule,
    MatSliderModule,
    MatSelectModule,
    MatFormFieldModule,
    MatButtonModule
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  isSidebarOpen = true;
  toggleSidebar() { this.isSidebarOpen = !this.isSidebarOpen; }
}