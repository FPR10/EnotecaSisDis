import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { Wine } from '../shared/models/wine.model';
import { WineService } from '../shared/services/wine.service';
import { SidebarFilter, WineFilterService } from '../shared/services/wine-filter.service';

@Component({
  selector: 'app-catalogo-vini',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './catalogo-vini.component.html',
  styleUrls: ['./catalogo-vini.component.scss']
})
export class CatalogoViniComponent implements OnInit, OnDestroy {
  filter: SidebarFilter | null = null;
  wines: Wine[] = [];
  isLoading = false;
  private filterSubscription?: Subscription;

  constructor(
    private wineService: WineService,
    private wineFilterService: WineFilterService
  ) {}

  ngOnInit(): void {
    this.filterSubscription = this.wineFilterService.filter$.subscribe(filter => {
      this.filter = filter;
      if (!filter) {
        this.wines = [];
        return;
      }
      this.isLoading = true;
      this.wineService.searchFromApi({ tipo: filter.type, regione: filter.region }).subscribe({
        next: wines => {
          this.wines = wines;
          this.isLoading = false;
        },
        error: () => {
          this.wines = [];
          this.isLoading = false;
        }
      });
    });
  }

  ngOnDestroy(): void {
    this.filterSubscription?.unsubscribe();
  }

  getBadgeClass(type: string): string {
    const map: Record<string, string> = {
      'Rosso':     'badge-rosso',
      'Bianco':    'badge-bianco',
      'Rosato':    'badge-rosato',
      'Bollicine': 'badge-bollicine',
    };
    return map[type] ?? 'badge-rosso';
  }
}
