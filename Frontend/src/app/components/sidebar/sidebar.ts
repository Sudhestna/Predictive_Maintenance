import { Component, inject, OnInit, ChangeDetectorRef, Input } from '@angular/core';
import { ApiService } from '../../services/api';
import { ToastService } from '../../services/toast';
import { ChatSession } from '../../models/chat-session';
import { SessionService } from '../../services/session';
import { Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css']
})
export class Sidebar implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private session = inject(SessionService);
  private cdr = inject(ChangeDetectorRef);
  private router = inject(Router);

  uploading = false;
  uploadFileName = '';
  sessions: ChatSession[] = [];
  currentSessionId = '';
  isSidebarOpen = true;
  @Input() isOpen = true;

  ngOnInit() {
    this.session.sessionId$.subscribe(id => {
      this.currentSessionId = id;
    });
    this.loadSessions();
  }

  loadSessions() {
    this.api.loadSessions().subscribe({
      next: (response) => {

          this.sessions = [...response];

          this.cdr.detectChanges();

          if (this.sessions.length === 0) {
              this.createSession();
              return;
          }

          if (!this.currentSessionId) {
              this.session.setSession(this.sessions[0].session_id);
          }

          this.cdr.detectChanges();
      },
      error: () => {
        this.toast.show('Unable to load sessions', 'error');
      }
    });
  }

  uploadDocument(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    const file = input.files[0];
    this.uploadFileName = file.name;
    this.uploading = true;

    this.api.uploadDocument(file).subscribe({
      next: () => {
        this.uploading = false;
        this.toast.show('Document ingested successfully.', 'success');
        input.value = '';
        this.uploadFileName = '';
      },
      error: () => {
        this.uploading = false;
        this.toast.show('Unable to upload document.', 'error');
        input.value = '';
        this.uploadFileName = '';
      }
    });
  }

  selectSession(sessionId: string) {
    this.session.setSession(sessionId);
  }

  createSession() {

    if (this.currentSessionId) {

      this.api.loadSession(this.currentSessionId).subscribe({

        next: (session) => {

          if (!session.messages || session.messages.length === 0) {

            this.toast.show(
              'Please send a message before creating a new session.',
              'info'
            );

            return;
          }

          this.createNewSession();

        },

        error: () => {
          this.toast.show(
            'Unable to verify current session.',
            'error'
          );
        }

      });

      return;
    }

    this.createNewSession();
  }

  private createNewSession() {

    this.api.createSession().subscribe({

      next: (response) => {

        this.toast.show(
          'New session created successfully.',
          'success'
        );

        this.loadSessions();

        setTimeout(() => {
          this.session.setSession(response.response);
        });

      },

      error: () => {

        this.toast.show(
          'Unable to create session.',
          'error'
        );

      }

    });

  }

  deleteSession(sessionId: string, event: MouseEvent) {
    event.stopPropagation();
    if (!confirm('Delete this session?')) return;

    this.api.deleteSession(sessionId).subscribe({
      next: () => {
        this.toast.show('Session deleted.', 'success');
        if (this.currentSessionId === sessionId) {
          this.session.setSession('');
        }
        this.loadSessions();
      },
      error: () => {
        this.toast.show('Unable to delete session.', 'error');
      }
    });
  }
   toggleSidebar() {
    this.isSidebarOpen = !this.isSidebarOpen;
  }
  goToSettings() {
    this.router.navigate(['/settings']);
  }
}
