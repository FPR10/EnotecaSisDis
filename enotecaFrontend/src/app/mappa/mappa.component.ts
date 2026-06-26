import { Component, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';
import { Subscription } from 'rxjs';
import { Wine } from '../shared/models/wine.model';
import { WineService } from '../shared/services/wine.service';
import { REGION_COORDINATES } from '../shared/data/region-coordinates';

//Apertura della mappa al centro tra nord e sud
const ITALY_CENTER: L.LatLngTuple = [42.8, 12.8];

//Regola lo zoom dell'inquadratura della mappa
const ITALY_ZOOM = 6;

//Numero di vini più popolari da mostrare nel popup di ogni regione
const TOP_WINES_PER_REGION = 3;

@Component({
  selector: 'app-mappa',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mappa.component.html',
  styleUrl: './mappa.component.scss'
})

export class MappaComponent implements AfterViewInit, OnDestroy {
  private map: L.Map | null = null;
  private wineSubscription: Subscription | null = null;

  constructor(private wineService: WineService) {}

  ngAfterViewInit(): void {
    this.map = L.map('mappa-leaflet').setView(ITALY_CENTER, ITALY_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: ' OpenStreetMap',
      maxZoom: 19
    }).addTo(this.map);

    setTimeout(() => this.map?.invalidateSize(), 0);

    this.wineSubscription = this.wineService.getAllFromApi().subscribe({
      next: wines => this.renderRegionMarkers(wines),
      error: err => console.error('Errore nel recupero dei vini per la mappa', err)
    });
  }

  ngOnDestroy(): void {
    this.wineSubscription?.unsubscribe();
    this.map?.remove();
    this.map = null;
  }

  private renderRegionMarkers(wines: Wine[]): void {
    if (!this.map) {
      return;
    }

    const winesByRegion = new Map<string, Wine[]>();
    for (const wine of wines) {
      if (!REGION_COORDINATES[wine.region]) {
        continue;
      }
      const group = winesByRegion.get(wine.region) ?? [];
      group.push(wine);
      winesByRegion.set(wine.region, group);
    }

    for (const region of Object.keys(REGION_COORDINATES)) {
      const centroid = REGION_COORDINATES[region];
      const regionWines = winesByRegion.get(region) ?? [];
      const popupHtml = this.buildTopWinesPopup(regionWines);

      L.circleMarker(centroid, {
        radius: 8,
        color: '#7a1f2b',
        weight: 1,
        fillColor: '#b5293a',
        fillOpacity: 0.7
      })
        .bindTooltip(region)
        .bindPopup(popupHtml)
        .addTo(this.map);
    }
  }

  private buildTopWinesPopup(regionWines: Wine[]): string {
    if (regionWines.length === 0) {
      return '<p>Nessun vino disponibile</p>';
    }

    const topWines = this.shuffle([...regionWines])
      .sort((a, b) => (b.popularity ?? 0) - (a.popularity ?? 0))
      .slice(0, TOP_WINES_PER_REGION);

    const items = topWines.map(wine => `<li>${wine.name}</li>`).join('');

    return `<ol>${items}</ol>`;
  }

  private shuffle<T>(items: T[]): T[] {
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [items[i], items[j]] = [items[j], items[i]];
    }
    return items;
  }
}
