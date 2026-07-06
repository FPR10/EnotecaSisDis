import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { Wine } from '../shared/models/wine.model';
import { WineService } from '../shared/services/wine.service';

@Component({
  selector: 'app-gestisci-vini',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './gestisci-vini.component.html',
  styleUrl: './gestisci-vini.component.scss'
})
export class GestisciViniComponent implements OnInit {
  wines: Wine[] = [];
  loading = false;
  loadError = '';
  deletingId: string | null = null;
  deleteErrorId: string | null = null;
  deleteError = '';
  confirmingId: string | null = null;
  totaleVini: number | null = null;
  searchTerm = '';
  priceSortDir: 'asc' | 'desc' | null = null;

  constructor(private wineService: WineService, private router: Router) {}

  ngOnInit(): void {
    this.wineService.getTotaleFromApi().subscribe({
      next: totale => { this.totaleVini = totale; }
    });
    this.loadWines();
  }

  get filteredWines(): Wine[] {
    const term = this.searchTerm.trim().toLowerCase();
    let result = term
      ? this.wines.filter(w => w.name?.toLowerCase().includes(term))
      : this.wines;
    if (this.priceSortDir) {
      result = [...result].sort((a, b) => {
        const priceA = a.price ?? 0;
        const priceB = b.price ?? 0;
        return this.priceSortDir === 'asc' ? priceA - priceB : priceB - priceA;
      });
    }
    return result;
  }

  togglePriceSort(): void {
    if (this.priceSortDir === null) {
      this.priceSortDir = 'asc';
    } else if (this.priceSortDir === 'asc') {
      this.priceSortDir = 'desc';
    } else {
      this.priceSortDir = null;
    }
  }

  loadWines(): void {
    this.loading = true;
    this.loadError = '';
    this.wineService.getAllFromApi().subscribe({
      next: wines => {
        this.wines = wines;
        this.loading = false;
      },
      error: () => {
        this.loadError = 'Impossibile caricare il catalogo. Riprova più tardi.';
        this.loading = false;
      }
    });
  }

  askConfirm(wineId: string): void {
    this.confirmingId = wineId;
  }

  cancelConfirm(): void {
    this.confirmingId = null;
  }

  confirmDelete(wineId: string): void {
    this.confirmingId = null;
    this.deletingId = wineId;
    this.deleteError = '';
    this.deleteErrorId = null;
    this.wineService.delete(wineId).subscribe({
      next: () => {
        this.wines = this.wines.filter(w => w.id !== wineId);
        this.deletingId = null;
      },
      error: (err: HttpErrorResponse) => {
        this.deletingId = null;
        this.deleteErrorId = wineId;
        this.deleteError = err.status === 404
          ? 'Il vino non esiste più (probabilmente già eliminato).'
          : 'Impossibile eliminare il vino. Riprova più tardi.';
      }
    });
  }

  onAddWine(): void {
    this.router.navigate(['/aggiungi-vino']);
  }
}