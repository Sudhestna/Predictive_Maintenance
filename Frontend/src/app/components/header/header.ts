import { Component, inject, OnInit, ChangeDetectorRef, Output, EventEmitter } from '@angular/core';
import { ApiService } from '../../services/api';
import { Router } from '@angular/router';

@Component({
  selector: 'app-header',
  templateUrl: './header.html',
  styleUrls: ['./header.css']
})
export class Header implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);
  private router = inject(Router);
  theme = 'light';

  @Output() toggleSidebar = new EventEmitter<void>();
  connected = false;
  checkingHealth = true;

  ngOnInit() {
    this.checkHealth();
  }

  ngAfterViewInit() {
    document.body.classList.remove('dark-theme');
    document.body.classList.add('light-theme');
    this.theme = 'light';
  }

  checkHealth() {
    this.api.health().subscribe({
      next: (response) => {
        this.connected = response.status;
        this.checkingHealth = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.connected = false;
        this.checkingHealth = false;
        this.cdr.detectChanges();
      }
    });
  }

  goToDashboard() {
    this.router.navigate(['/dashboard']);
  }

  goToChat() {
    this.router.navigate(['/chat']);
  }
  goToAnalytics() {
    this.router.navigate(['/analytics']);
  }
  goToSettings() {
    this.router.navigate(['/settings']);
  }
  

  themeChange() {
    if (this.theme === 'light') {
      document.body.classList.remove('light-theme');
      document.body.classList.add('dark-theme');
      this.theme = 'dark';
    } else {
      document.body.classList.remove('dark-theme');
      document.body.classList.add('light-theme');
      this.theme = 'light';
    }
  }

  goToProfile() {
    this.router.navigate(['/profile']);
  }
}
