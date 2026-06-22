import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, NgForm } from '@angular/forms';
import { Router } from '@angular/router';
import { Wine, WineType } from '../shared/models/wine.model';
import { WineService } from '../shared/services/wine.service';

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
  imageUrl: string;
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
    imageUrl: ''
  };

  imagePreview: string | null = null;
  formError = '';

  constructor(private wineService: WineService, private router: Router) {}

  get checklist(): { label: string; done: boolean }[] {
    return [
      { label: 'Nome vino', done: !!this.form.name.trim() },
      { label: 'Produttore', done: !!this.form.producer.trim() },
      { label: 'Annata', done: !!this.form.year },
      { label: 'Descrizione', done: !!this.form.description.trim() },
      { label: 'Immagine etichetta', done: !!this.imagePreview }
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
    const reader = new FileReader();
    reader.onload = e => {
      this.imagePreview = e.target?.result as string;
      this.form.imageUrl = this.imagePreview;
    };
    reader.readAsDataURL(file);
  }

  clearImage(): void {
    this.imagePreview = null;
    this.form.imageUrl = '';
  }

  onSubmit(wineForm: NgForm): void {
    if (wineForm.invalid || !this.form.type) {
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
      imageUrl: this.form.imageUrl || undefined
    };

    this.wineService.add(wine);
    this.router.navigate(['/']);
  }

  onCancel(): void {
    this.router.navigate(['/']);
  }
}
