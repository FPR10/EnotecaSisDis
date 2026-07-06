import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { Wine } from '../shared/models/wine.model';
import { WineService } from '../shared/services/wine.service';
import { CatalogSource, WineFilterService } from '../shared/services/wine-filter.service';

@Component({
  selector: 'app-catalogo-vini',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './catalogo-vini.component.html',
  styleUrls: ['./catalogo-vini.component.scss']
})
export class CatalogoViniComponent implements OnInit, OnDestroy {
  source: CatalogSource | null = null;
  wines: Wine[] = [];
  isLoading = false;
  private filterSubscription?: Subscription;

  constructor(
    private wineService: WineService,
    private wineFilterService: WineFilterService
  ) {}

  ngOnInit(): void {
    this.filterSubscription = this.wineFilterService.filter$.subscribe(source => {
      this.source = source;
      if (!source) {
        this.wines = [];
        return;
      }
      if (source.kind === 'search') {
        this.wines = source.wines;
        this.isLoading = false;
        return;
      }
      this.isLoading = true;
      this.wineService.searchFromApi({ tipo: source.type, regione: source.region }).subscribe({
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

  get breadcrumbLabel(): string {
    if (!this.source) return 'Vini';
    return this.source.kind === 'sidebar' ? `${this.source.type} · ${this.source.region}` : this.source.label;
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