import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet } from '@angular/router';
import { NavbarComponent } from './navbar/navbar.component';
import { SidebarComponent } from './sidebar/sidebar.component';
import { WineFilterService } from './shared/services/wine-filter.service';
import { WineType } from './shared/models/wine.model';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, NavbarComponent, SidebarComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})


export class AppComponent {
  constructor(private router: Router, private wineFilterService: WineFilterService) {}

  onManageWines(): void {
    this.router.navigate(['/gestisci-vini']);
  }

  onFilterChange(filter: { type: string; region?: string }): void {
    if (!filter.region) return;
    this.wineFilterService.setFilter({ type: filter.type as WineType, region: filter.region });
    this.router.navigate(['/catalogo']);
  }

  onMapClick(): void {
    this.router.navigate(['/mappa']);
  }
}
