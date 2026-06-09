import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Category } from '../shared/models/category.model';

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
    { name: 'Rosso',     color: '#e05252', regions: ['Toscana', 'Piemonte', 'Sicilia', 'Calabria'], expanded: true },
    { name: 'Bianco',    color: '#e0b852', regions: ['Campania', 'Friuli', 'Sicilia'],               expanded: false },
    { name: 'Rosato',    color: '#e07c52', regions: ['Abruzzo', 'Puglia'],                           expanded: false },
    { name: 'Bollicine', color: '#52b0e0', regions: ['Lombardia', 'Trentino'],                       expanded: false },
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
