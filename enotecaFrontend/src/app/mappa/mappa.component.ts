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

//Raggio (in gradi) entro cui disperdere i puntini di uno stesso vino/regione, per il look "a nube"
const CLOUD_JITTER_DEGREES = 0.25;

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
      next: wines => this.renderWineCloud(wines),
      error: err => console.error('Errore nel recupero dei vini per la mappa', err)
    });
  }

  ngOnDestroy(): void {
    this.wineSubscription?.unsubscribe();
    this.map?.remove();
    this.map = null;
  }

  private renderWineCloud(wines: Wine[]): void {
    if (!this.map) {
      return;
    }

    const winesByRegion = new Map<string, Wine[]>();
    for (const wine of wines) {
      const centroid = REGION_COORDINATES[wine.region];
      if (!centroid) {
        continue;
      }
      const group = winesByRegion.get(wine.region) ?? [];
      group.push(wine);
      winesByRegion.set(wine.region, group);
    }

    for (const [region, regionWines] of winesByRegion) {
      const centroid = REGION_COORDINATES[region];
      const popupHtml = this.buildTopWinesPopup(region, regionWines);

      for (const wine of regionWines) {
        const point: L.LatLngTuple = [
          centroid[0] + (Math.random() - 0.5) * CLOUD_JITTER_DEGREES,
          centroid[1] + (Math.random() - 0.5) * CLOUD_JITTER_DEGREES
        ];

        L.circleMarker(point, {
          radius: 5,
          color: '#7a1f2b',
          weight: 1,
          fillColor: '#b5293a',
          fillOpacity: 0.7
        })
          .bindTooltip(wine.name)
          .bindPopup(popupHtml)
          .addTo(this.map);
      }
    }
  }

  private buildTopWinesPopup(region: string, regionWines: Wine[]): string {
    const topWines = [...regionWines]
      .sort((a, b) => (b.popularity ?? 0) - (a.popularity ?? 0) || a.name.localeCompare(b.name))
      .slice(0, TOP_WINES_PER_REGION);

    const items = topWines
      .map(wine => `<li>${wine.name} <small>(${wine.producer})</small></li>`)
      .join('');

    return `
      <strong>${region}</strong> — ${regionWines.length} vini
      <ol>${items}</ol>
    `;
  }
}
