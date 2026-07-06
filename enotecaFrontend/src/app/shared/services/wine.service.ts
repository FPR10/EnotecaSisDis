import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map, switchMap, timeout, shareReplay } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Wine, WineApi, WineType, WINE_TYPE_TO_API, wineFromApi, wineToApiCreate } from '../models/wine.model';

interface WinePageApi {
  items: WineApi[];
  total: number;
  skip: number;
  limit: number;
}

export interface WineSearchFilter {
  tipo?: WineType;
  regione?: string;
  denominazione?: string;
  q?: string;
}

export interface BulkImportResult {
  created: number;
  errors: { riga: number; errore: string }[];
}

@Injectable({ providedIn: 'root' })
export class WineService {
  private readonly baseUrl = `${environment.apiBaseUrl}/wines`;
  private allWines$: Observable<Wine[]> | null = null;

  constructor(private http: HttpClient) {}

  getTotaleFromApi(): Observable<number> {
    return this.http
      .get<WinePageApi>(this.baseUrl, { params: { skip: 0, limit: 1 } })
      .pipe(map(page => page.total));
  }

  searchFromApi(filtro: WineSearchFilter): Observable<Wine[]> {
    const params: Record<string, string> = {};
    if (filtro.tipo) params['tipo'] = WINE_TYPE_TO_API[filtro.tipo];
    if (filtro.regione) params['regione'] = filtro.regione;
    if (filtro.denominazione) params['denominazione'] = filtro.denominazione;
    if (filtro.q) params['q'] = filtro.q;
    return this.http
      .get<WinePageApi>(this.baseUrl, { params: { ...params, skip: 0, limit: 50 } })
      .pipe(map(page => page.items.map(wineFromApi)));
  }

  getFeaturedFromApi(): Observable<Wine[]> {
  return this.getAllFromApi().pipe(
    map(wines => {
      const winesByType = new Map<WineType, Wine[]>();
      for (const wine of wines) {
        const group = winesByType.get(wine.type);
        if (group) group.push(wine);
        else winesByType.set(wine.type, [wine]);
      }

      return Array.from(winesByType.values()).map(group => {
        // prendi i top 5 per popolarità di ogni tipo
        const top5 = [...group]
          .sort((a, b) => (b.popularity ?? 0) - (a.popularity ?? 0))
          .slice(0, 5);
        // scegli 1 a caso tra i top 5
        return top5[Math.floor(Math.random() * top5.length)];
      });
    })
  );
}

  add(wine: Wine): Observable<Wine> {
    return this.http
      .post<WineApi>(this.baseUrl, wineToApiCreate(wine))
      .pipe(map(w => { this.clearCache(); return wineFromApi(w); }));
  }

  delete(wineId: string): Observable<void> {
    return this.http
      .delete<void>(`${this.baseUrl}/${wineId}`)
      .pipe(map(() => { this.clearCache(); }));
  }

  uploadImage(wineId: string, file: File): Observable<Wine> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http
      .post<WineApi>(`${this.baseUrl}/${wineId}/image`, formData)
      .pipe(map(wineFromApi));
  }

  bulkImport(file: File): Observable<BulkImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http
      .post<BulkImportResult>(`${this.baseUrl}/bulk-import`, formData)
      .pipe(timeout(600000));
  }

  getAllFromApi(): Observable<Wine[]> {
    if (!this.allWines$) {
      this.allWines$ = this.http
        .get<WinePageApi>(this.baseUrl, { params: { skip: 0, limit: 1 } })
        .pipe(
          switchMap(firstPage =>
            this.http.get<WinePageApi>(this.baseUrl, {
              params: { skip: 0, limit: firstPage.total || 1 },
            })
          ),
          map(page => page.items.map(wineFromApi)),
          shareReplay(1)
        );
    }
    return this.allWines$;
  }

  clearCache(): void {
    this.allWines$ = null;
  }
}