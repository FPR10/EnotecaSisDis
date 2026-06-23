import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { OcrSearchOut } from '../models/ocr.model';

@Injectable({ providedIn: 'root' })
export class OcrService {
  private readonly baseUrl = `${environment.apiBaseUrl}/ocr`;

  constructor(private http: HttpClient) {}

  riconosciEtichetta(immagine: File): Observable<OcrSearchOut> {
    const formData = new FormData();
    formData.append('immagine', immagine);
    return this.http.post<OcrSearchOut>(`${this.baseUrl}/etichetta`, formData);
  }
}
