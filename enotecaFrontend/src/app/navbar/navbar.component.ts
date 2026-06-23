import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MsalService } from '@azure/msal-angular';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent {
  @Output() addWineClick = new EventEmitter<void>();

  constructor(private router: Router, private msalService: MsalService) {}

  get isLoggedIn(): boolean {
    return !!this.msalService.instance.getActiveAccount();
  }

  goHome(): void {
    this.router.navigate(['/']);
  }

  onAddWine(): void {
    this.addWineClick.emit();
  }

  contactUS(): void {
    this.router.navigate(['/contact']);
  }

  logout(): void {
    this.msalService.logoutRedirect();
  }
}
