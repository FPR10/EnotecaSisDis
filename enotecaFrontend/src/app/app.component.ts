import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { NavbarComponent } from './navbar/navbar.component';
import { SidebarComponent } from './sidebar/sidebar.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, NavbarComponent, SidebarComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  onAddWine(): void {
    // Aprirà una modale / navigherà a una form di inserimento
    console.log('Aggiungi vino');
  }

  onFilterChange(filter: { type: string; region?: string }): void {
    console.log('Filtro applicato:', filter);
    // Propagherà il filtro a HomeComponent (via service o @Input)
  }

  onMapClick(): void {
    console.log('Apri mappa');
  }
}
