import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { WineType } from '../models/wine.model';

export interface SidebarFilter {
  type: WineType;
  region: string;
}

/** Propaga il filtro selezionato nella sidebar (tipo + regione) alla home, che ne mostra i risultati. */
@Injectable({ providedIn: 'root' })
export class WineFilterService {
  private readonly filterSubject = new BehaviorSubject<SidebarFilter | null>(null);
  readonly filter$ = this.filterSubject.asObservable();

  setFilter(filter: SidebarFilter): void {
    this.filterSubject.next(filter);
  }
}
