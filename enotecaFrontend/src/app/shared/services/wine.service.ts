import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map, switchMap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Wine, WineApi, WineType, WINE_TYPE_TO_API, wineFromApi, wineToApiCreate } from '../models/wine.model';

interface WinePageApi {
  items: WineApi[];
  total: number;
  skip: number;
  limit: number;
}

/** Filtri di ricerca testuale/sidebar, tradotti nei query params di GET /wines. */
export interface WineSearchFilter {
  tipo?: WineType;
  regione?: string;
  denominazione?: string;
  q?: string;
}

/** Esito dell'import massivo (POST /wines/bulk-import): conteggio creati + righe scartate con il relativo errore. */
export interface BulkImportResult {
  created: number;
  errors: { riga: number; errore: string }[];
}

@Injectable({ providedIn: 'root' })
export class WineService {
  private readonly baseUrl = `${environment.apiBaseUrl}/wines`;

  constructor(private http: HttpClient) {}

  /** Ricerca testuale/per filtri sul backend (GET /wines), usata dalla ricerca in home e dai filtri della sidebar. */
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

  /**
   * Vini "consigliati" per la home: per ogni chiamata sceglie a caso 3 tipologie tra quelle presenti
   * in catalogo e per ciascuna restituisce il vino con la valutazione (popolarità) più alta.
   */
  getFeaturedFromApi(): Observable<Wine[]> {
    return this.getAllFromApi().pipe(
      map(wines => {
        const winesByType = new Map<WineType, Wine[]>();
        for (const wine of wines) {
          const group = winesByType.get(wine.type);
          if (group) group.push(wine);
          else winesByType.set(wine.type, [wine]);
        }

        const types = Array.from(winesByType.keys())
          .sort(() => Math.random() - 0.5)
          .slice(0, 3);

        return types.map(type =>
          [...winesByType.get(type)!].sort((a, b) => (b.popularity ?? 0) - (a.popularity ?? 0))[0]
        );
      })
    );
  }

  /** Crea il vino sul backend (POST /wines, riservato agli admin) e restituisce il vino creato. */
  add(wine: Wine): Observable<Wine> {
    return this.http.post<WineApi>(this.baseUrl, wineToApiCreate(wine)).pipe(map(wineFromApi));
  }

  /** Elimina il vino dal backend (DELETE /wines/{id}, riservato agli admin). */
  delete(wineId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${wineId}`);
  }

  /**
   * Carica l'immagine etichetta su Blob Storage (POST /wines/{id}/image, riservato agli admin)
   * e restituisce il vino aggiornato con l'URL del blob salvato in immagine_etichetta.
   */
  uploadImage(wineId: string, file: File): Observable<Wine> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<WineApi>(`${this.baseUrl}/${wineId}/image`, formData).pipe(map(wineFromApi));
  }

  /** Importa più vini in massa da un file CSV o JSON (POST /wines/bulk-import, riservato agli admin). */
  bulkImport(file: File): Observable<BulkImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<BulkImportResult>(`${this.baseUrl}/bulk-import`, formData);
  }

  /** Recupera dal backend l'intero catalogo (tutte le pagine), per usi come la distribuzione in mappa. */
  getAllFromApi(): Observable<Wine[]> {
    return this.http.get<WinePageApi>(this.baseUrl, { params: { skip: 0, limit: 1 } }).pipe(
      switchMap(firstPage =>
        this.http.get<WinePageApi>(this.baseUrl, { params: { skip: 0, limit: firstPage.total || 1 } })
      ),
      map(page => page.items.map(wineFromApi))
    );
  }
}
