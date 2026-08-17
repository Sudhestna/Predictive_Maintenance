import {
  Component,
  EventEmitter,
  Input,
  Output
} from '@angular/core';

import {
  DomSanitizer,
  SafeResourceUrl
} from '@angular/platform-browser';

@Component({
  selector: 'app-preview-drawer',
  imports: [],
  templateUrl: './preview-drawer.html',
  styleUrl: './preview-drawer.css',
  standalone: true
})
export class PreviewDrawer {

  safePdfUrl: SafeResourceUrl = '';

  @Input()
  isOpen = false;

  @Input()
  title = "";

  @Input()
  chunks: string[] = [];

  private _pdfUrl = "";

  @Input()
  set pdfUrl(value: string) {

    this._pdfUrl = value || "";

    if (this._pdfUrl) {

      // Add a cache-busting parameter here as an additional safeguard.
      const separator = this._pdfUrl.includes("?") ? "&" : "?";

      const freshUrl =
        `${this._pdfUrl}${separator}t=${Date.now()}`;

      console.log("Preview PDF URL:", freshUrl);

      this.safePdfUrl =
        this.sanitizer.bypassSecurityTrustResourceUrl(freshUrl);

    } else {

      this.safePdfUrl = "";

    }
  }

  get pdfUrl(): string {
    return this._pdfUrl;
  }

  @Output()
  close = new EventEmitter<void>();

  constructor(
    private sanitizer: DomSanitizer
  ) {}
}