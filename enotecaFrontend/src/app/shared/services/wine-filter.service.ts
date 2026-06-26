import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Wine, WineType } from '../models/wine.model';

export interface SidebarFilter {
  type: WineType;
  region: string;
}

/** Filtro per tipo+regione (sidebar) o lista di risultati già ottenuti (ricerca in home), mostrati dal catalogo. */
export type CatalogSource =
  | ({ kind: 'sidebar' } & SidebarFilter)
  | { kind: 'search'; label: string; wines: Wine[] };

/** Propaga al catalogo il filtro selezionato nella sidebar o i risultati di una ricerca fatta in home. */
@Injectable({ providedIn: 'root' })
export class WineFilterService {
  private readonly filterSubject = new BehaviorSubject<CatalogSource | null>(null);
  readonly filter$ = this.filterSubject.asObservable();

  setSidebarFilter(filter: SidebarFilter): void {
    this.filterSubject.next({ kind: 'sidebar', ...filter });
  }

  setSearchResults(label: string, wines: Wine[]): void {
    this.filterSubject.next({ kind: 'search', label, wines });
  }
}
