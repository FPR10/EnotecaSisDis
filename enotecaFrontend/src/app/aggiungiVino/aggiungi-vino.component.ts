import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule, NgForm } from '@angular/forms';
import { Router } from '@angular/router';
import { Wine, WineType } from '../shared/models/wine.model';
import { BulkImportResult, WineService } from '../shared/services/wine.service';

interface WineFormModel {
  name: string;
  producer: string;
  year: number | null;
  type: WineType | '';
  denomination: string;
  grapeVariety: string;
  region: string;
  country: string;
  description: string;
  price: number | null;
  quantity: number | null;
  available: boolean;
  rating: number | null;
}

@Component({
  selector: 'app-aggiungi-vino',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './aggiungi-vino.component.html',
  styleUrl: './aggiungi-vino.component.scss'
})


export class AggiungiVinoComponent {

  readonly types: WineType[] = ['Rosso', 'Bianco', 'Rosato', 'Bollicine'];

  readonly regions: string[] = [
  'Abruzzo', 'Basilicata', 'Calabria', 'Campania', 'Emilia-Romagna',
  'Friuli-Venezia Giulia', 'Lazio', 'Liguria', 'Lombardia', 'Marche',
  'Molise', 'Piemonte', 'Puglia', 'Sardegna', 'Sicilia',
  'Toscana', 'Trentino-Alto Adige', 'Umbria', 'Valle d\'Aosta', 'Veneto'
  ];

  form: WineFormModel = {
    name: '',
    producer: '',
    year: null,
    type: '',
    denomination: '',
    grapeVariety: '',
    region: '',
    country: 'Italia',
    description: '',
    price: null,
    quantity: null,
    available: true,
    rating: null
  };

  readonly ratingOptions = [1, 2, 3, 4, 5];

  imagePreview: string | null = null;
  selectedImageFile: File | null = null;
  formError = '';
  saving = false;

  /** Colonne riconosciute dal backend per l'import massivo (campi di WineCreate, vedi POST /wines/bulk-import). */
  readonly bulkExpectedColumns = [
    'nome', 'produttore', 'azienda_vinicola', 'tipo', 'regione',
    'annata', 'denominazione', 'vitigno', 'prezzo', 'scorte',
    'descrizione', 'disponibile', 'popolarita', 'immagine_etichetta'
  ];

  /** Sottoinsieme obbligatorio in WineCreate: nome, produttore, azienda_vinicola, regione, tipo. */
  readonly bulkRequiredColumns = ['nome', 'produttore', 'azienda_vinicola', 'tipo', 'regione'];

  get bulkRequiredHint(): string {
    return this.bulkRequiredColumns
      .map(c => c === 'tipo' ? 'tipo (rosso/bianco/rosato/bollicine)' : c)
      .join(', ');
  }

  selectedBulkFile: File | null = null;
  bulkUploading = false;
  bulkError = '';
  bulkResult: BulkImportResult | null = null;

  constructor(private wineService: WineService, private router: Router) {}

  get checklist(): { label: string; done: boolean }[] {
    return [
      { label: 'Nome vino', done: !!this.form.name.trim() },
      { label: 'Produttore', done: !!this.form.producer.trim() },
      { label: 'Annata', done: !!this.form.year },
      { label: 'Descrizione', done: !!this.form.description.trim() },
      { label: 'Immagine etichetta', done: !!this.imagePreview },
      { label: 'Valutazione qualità', done: !!this.form.rating }
    ];
  }

  get completenessPercent(): number {
    const items = this.checklist;
    const done = items.filter(i => i.done).length;
    return Math.round((done / items.length) * 100);
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
    this.selectedImageFile = file;
    const reader = new FileReader();
    reader.onload = e => {
      this.imagePreview = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  }

  clearImage(): void {
    this.imagePreview = null;
    this.selectedImageFile = null;
  }

  onSubmit(wineForm: NgForm): void {
    if (wineForm.invalid || !this.form.type || !this.form.rating) {
      this.formError = 'Compila tutti i campi obbligatori (*) prima di salvare.';
      return;
    }
    this.formError = '';

    const wine: Wine = {
      id: crypto.randomUUID(),
      name: this.form.name.trim(),
      producer: this.form.producer.trim(),
      winery: this.form.producer.trim(),
      year: this.form.year ?? undefined,
      type: this.form.type,
      denomination: this.form.denomination.trim() || undefined,
      grapeVariety: this.form.grapeVariety.trim() || undefined,
      region: this.form.region,
      country: this.form.country.trim() || undefined,
      description: this.form.description.trim() || undefined,
      price: this.form.price ?? undefined,
      quantity: this.form.quantity ?? undefined,
      available: this.form.available,
      popularity: this.form.rating ?? undefined
    };

    this.saving = true;
    this.wineService.add(wine).subscribe({
      next: created => {
        if (this.selectedImageFile) {
          this.wineService.uploadImage(created.id, this.selectedImageFile).subscribe({
            next: () => this.router.navigate(['/']),
            // il vino è già stato creato: un'eventuale immagine non caricata non blocca il salvataggio
            error: () => this.router.navigate(['/'])
          });
        } else {
          this.router.navigate(['/']);
        }
      },
      error: (err: HttpErrorResponse) => {
        this.saving = false;
        this.formError = this.extractErrorMessage(err);
      }
    });
  }

  onBulkFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) this.setBulkFile(file);
    input.value = '';
  }

  onBulkFileDrop(event: DragEvent): void {
    event.preventDefault();
    const file = event.dataTransfer?.files[0];
    if (file) this.setBulkFile(file);
  }

  private setBulkFile(file: File): void {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (extension !== 'csv' && extension !== 'json') {
      this.bulkError = 'Formato non supportato: usa un file .csv o .json.';
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      this.bulkError = 'Il file supera la dimensione massima di 25 MB.';
      return;
    }
    this.bulkError = '';
    this.bulkResult = null;
    this.selectedBulkFile = file;
  }

  clearBulkFile(): void {
    this.selectedBulkFile = null;
    this.bulkError = '';
    this.bulkResult = null;
  }

  uploadBulkFile(): void {
    if (!this.selectedBulkFile) return;
    this.bulkUploading = true;
    this.bulkError = '';
    this.bulkResult = null;

    this.wineService.bulkImport(this.selectedBulkFile).subscribe({
      next: result => {
        this.bulkUploading = false;
        this.bulkResult = result;
        this.selectedBulkFile = null;
      },
      error: (err: HttpErrorResponse) => {
        this.bulkUploading = false;
        this.bulkError = this.extractErrorMessage(err);
      }
    });
  }

  private extractErrorMessage(err: HttpErrorResponse): string {
    const detail = err.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(', ');
    }
    return 'Impossibile salvare il vino. Riprova più tardi.';
  }

  onCancel(): void {
    this.router.navigate(['/']);
  }
}
