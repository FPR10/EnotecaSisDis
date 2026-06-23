import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AbbinamentoOut } from '../models/pairing.model';

@Injectable({ providedIn: 'root' })
export class PairingService {
  private readonly baseUrl = `${environment.apiBaseUrl}/pairing`;

  constructor(private http: HttpClient) {}

  abbina(cibo: string): Observable<AbbinamentoOut> {
    return this.http.post<AbbinamentoOut>(`${this.baseUrl}/abbinamento`, { cibo });
  }
}
