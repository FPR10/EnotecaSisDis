import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Category } from '../shared/models/category.model';
import { REGION_COORDINATES } from '../shared/data/region-coordinates';

//Regioni italiane in ordine alfabetico, comuni a tutte le categorie di vino
const REGIONS = Object.keys(REGION_COORDINATES).sort((a, b) => a.localeCompare(b));

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent {
  @Output() filterChange = new EventEmitter<{ type: string; region?: string }>();
  @Output() mapClick = new EventEmitter<void>();

  categories: Category[] = [
    { name: 'Rosso',     color: '#e05252', regions: REGIONS, expanded: true },
    { name: 'Bianco',    color: '#e0b852', regions: REGIONS, expanded: false },
    { name: 'Rosato',    color: '#e07c52', regions: REGIONS, expanded: false },
    { name: 'Bollicine', color: '#52b0e0', regions: REGIONS, expanded: false },
  ];

  toggleCategory(cat: Category): void {
    cat.expanded = !cat.expanded;
  }

  selectType(type: string): void {
    this.filterChange.emit({ type });
  }

  selectRegion(type: string, region: string): void {
    this.filterChange.emit({ type, region });
  }

  openMap(): void {
    this.mapClick.emit();
  }
}
