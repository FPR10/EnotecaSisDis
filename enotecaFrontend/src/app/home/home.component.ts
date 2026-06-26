import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Wine, WineType, wineFromApi } from '../shared/models/wine.model';
import { WineSearchFilter, WineService } from '../shared/services/wine.service';
import { PairingService } from '../shared/services/pairing.service';
import { VinoSuggerito } from '../shared/models/pairing.model';
import { OcrService } from '../shared/services/ocr.service';
import { WineFilterService } from '../shared/services/wine-filter.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  featuredWines: Wine[] = [];

  // abbinamento cibo-vino
  foodQuery = '';
  pairingSuggestions: VinoSuggerito[] = [];
  pairingError = '';
  isLoadingPairing = false;

  // ricerca testuale
  searchTab: 'text' | 'image' = 'text';
  searchField = 'q';
  searchQuery = '';
  isLoadingSearch = false;
  searchError = '';

  // ricerca per immagine
  imageFile: File | null = null;
  imagePreview: string | null = null;
  imageSearchError = '';

  constructor(
    private wineService: WineService,
    private pairingService: PairingService,
    private ocrService: OcrService,
    private wineFilterService: WineFilterService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.wineService.getFeaturedFromApi().subscribe({
      next: wines => { this.featuredWines = wines; },
      error: err => console.error('Errore nel recupero dei vini consigliati', err)
    });
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

  /** Immagine fissa per tipologia di vino (non l'etichetta del singolo vino, sempre la stessa per tipo). */
  getCardImage(type: string): string {
    const map: Record<string, string> = {
      'Rosso':     'assets/wine-types/rosso.jpg',
      'Bianco':    'assets/wine-types/bianco.jpg',
      'Rosato':    'assets/wine-types/rosato.jpg',
      'Bollicine': 'assets/wine-types/bollicine.jpg',
    };
    return map[type] ?? 'assets/wine-types/rosso.jpg';
  }

  getSearchPlaceholder(): string {
    const map: Record<string, string> = {
      'q':             'Nome, produttore, vitigno...',
      'nome':          'es. Barolo, Marchesi di Barolo...',
      'regione':       'es. Toscana, Piemonte...',
      'denominazione': 'es. DOCG, Barolo DOCG...',
    };
    return map[this.searchField] ?? 'Cerca...';
  }

  onPairing(): void {
    if (!this.foodQuery.trim()) return;
    this.isLoadingPairing = true;
    this.pairingError = '';
    this.pairingSuggestions = [];
    this.pairingService.abbina(this.foodQuery.trim()).subscribe({
      next: (risposta) => {
        this.pairingSuggestions = risposta.suggerimenti;
        this.isLoadingPairing = false;
      },
      error: (err) => {
        this.pairingError = err?.error?.detail ?? 'Abbinamento non disponibile al momento. Riprova più tardi.';
        this.isLoadingPairing = false;
      }
    });
  }

  capitalize(value: string): string {
    return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
  }

  onSearch(): void {
    const query = this.searchQuery.trim();
    if (!query) return;
    this.isLoadingSearch = true;
    this.searchError = '';
    this.wineService.searchFromApi(this.buildSearchFilter(query)).subscribe({
      next: wines => {
        this.isLoadingSearch = false;
        this.wineFilterService.setSearchResults(this.buildSearchLabel(query), wines);
        this.router.navigate(['/catalogo']);
      },
      error: () => {
        this.isLoadingSearch = false;
        this.searchError = 'Ricerca non disponibile al momento. Riprova più tardi.';
      }
    });
  }

  private buildSearchFilter(query: string): WineSearchFilter {
    switch (this.searchField) {
      case 'tipo': return { tipo: query as WineType };
      case 'nome': return { q: query };
      case 'regione': return { regione: query };
      case 'denominazione': return { denominazione: query };
      default: return { q: query };
    }
  }

  private buildSearchLabel(query: string): string {
    const fieldLabel: Record<string, string> = {
      q: 'Ricerca',
      nome: 'Nome / Produttore',
      tipo: 'Tipo',
      regione: 'Regione',
      denominazione: 'Denominazione',
    };
    return `${fieldLabel[this.searchField] ?? 'Ricerca'}: "${query}"`;
  }

  onImageSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) this.loadImageFile(file);
  }

  onImageDrop(event: DragEvent): void {
    event.preventDefault();
    const file = event.dataTransfer?.files[0];
    if (file && ['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      this.loadImageFile(file);
    }
  }

  private loadImageFile(file: File): void {
    this.imageFile = file;
    this.imageSearchError = '';
    const reader = new FileReader();
    reader.onload = e => { this.imagePreview = e.target?.result as string; };
    reader.readAsDataURL(file);
  }

  onImageSearch(): void {
    if (!this.imageFile) return;
    this.isLoadingSearch = true;
    this.imageSearchError = '';
    this.ocrService.riconosciEtichetta(this.imageFile).subscribe({
      next: (risposta) => {
        this.isLoadingSearch = false;
        const wines = risposta.results.map(wineFromApi);
        const label = risposta.extracted_text
          ? `Ricerca per etichetta: «${risposta.extracted_text}»`
          : 'Ricerca per etichetta';
        this.wineFilterService.setSearchResults(label, wines);
        this.router.navigate(['/catalogo']);
      },
      error: (err) => {
        this.imageSearchError = err?.error?.detail ?? 'Riconoscimento etichetta non disponibile al momento. Riprova più tardi.';
        this.isLoadingSearch = false;
      }
    });
  }

  clearImage(): void {
    this.imageFile = null;
    this.imagePreview = null;
    this.imageSearchError = '';
  }
}
