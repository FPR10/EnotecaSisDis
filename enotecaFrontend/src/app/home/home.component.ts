import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Wine, wineFromApi } from '../shared/models/wine.model';
import { WineService } from '../shared/services/wine.service';
import { PairingService } from '../shared/services/pairing.service';
import { VinoSuggerito } from '../shared/models/pairing.model';
import { OcrService } from '../shared/services/ocr.service';

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
  searchResults: Wine[] = [];
  isLoadingSearch = false;
  hasSearched = false;

  // ricerca per immagine
  imageFile: File | null = null;
  imagePreview: string | null = null;
  imageSearchError = '';
  extractedText = '';

  constructor(
    private wineService: WineService,
    private pairingService: PairingService,
    private ocrService: OcrService
  ) {}

  ngOnInit(): void {
    this.featuredWines = this.wineService.getFeatured().slice(0, 3);
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

  getCardBg(type: string): string {
    const map: Record<string, string> = {
      'Rosso':     '#fde8e8',
      'Bianco':    '#fdf6e3',
      'Rosato':    '#fde8e0',
      'Bollicine': '#e3f0fd',
    };
    return map[type] ?? '#f5f5f5';
  }

  getBottleColor(type: string): string {
    const map: Record<string, string> = {
      'Rosso':     '#c0392b',
      'Bianco':    '#a07820',
      'Rosato':    '#c05020',
      'Bollicine': '#1a6bad',
    };
    return map[type] ?? '#aaa';
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
    if (!this.searchQuery.trim()) return;
    this.isLoadingSearch = true;
    setTimeout(() => {
      this.searchResults = this.wineService.searchByField(this.searchField, this.searchQuery);
      this.hasSearched = true;
      this.isLoadingSearch = false;
    }, 300);
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
    this.hasSearched = false;
    this.searchResults = [];
    this.imageSearchError = '';
    this.extractedText = '';
    const reader = new FileReader();
    reader.onload = e => { this.imagePreview = e.target?.result as string; };
    reader.readAsDataURL(file);
  }

  onImageSearch(): void {
    if (!this.imageFile) return;
    this.isLoadingSearch = true;
    this.imageSearchError = '';
    this.extractedText = '';
    this.ocrService.riconosciEtichetta(this.imageFile).subscribe({
      next: (risposta) => {
        this.extractedText = risposta.extracted_text;
        this.searchResults = risposta.results.map(wineFromApi);
        this.hasSearched = true;
        this.isLoadingSearch = false;
      },
      error: (err) => {
        this.imageSearchError = err?.error?.detail ?? 'Riconoscimento etichetta non disponibile al momento. Riprova più tardi.';
        this.hasSearched = false;
        this.isLoadingSearch = false;
      }
    });
  }

  clearImage(): void {
    this.imageFile = null;
    this.imagePreview = null;
    this.searchResults = [];
    this.hasSearched = false;
    this.imageSearchError = '';
    this.extractedText = '';
  }
}
