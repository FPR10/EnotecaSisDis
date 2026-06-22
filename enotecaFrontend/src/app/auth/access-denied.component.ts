import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-accesso-negato',
  standalone: true,
  template: `
    <div class="access-denied">
      <h2>Accesso negato</h2>
      <p>Il tuo account non ha i permessi di amministratore necessari per aggiungere un vino.</p>
      <button (click)="goHome()">Torna alla home</button>
    </div>
  `,
  styles: [`
    .access-denied {
      padding: 3rem 2rem;
      text-align: center;
    }
  `]
})
export class AccessDeniedComponent {
  constructor(private router: Router) {}

  goHome(): void {
    this.router.navigate(['/']);
  }
}
