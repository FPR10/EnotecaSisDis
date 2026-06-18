import { Component, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';

//Apertura della mappa al centro tra nord e sud
const ITALY_CENTER: L.LatLngTuple = [42.8, 12.8];

//Regola lo zoom dell'inquadratura della mappa
const ITALY_ZOOM = 6;

@Component({
  selector: 'app-mappa',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mappa.component.html',
  styleUrl: './mappa.component.scss'
})

export class MappaComponent implements AfterViewInit, OnDestroy {
  private map: L.Map | null = null;

  ngAfterViewInit(): void {
    this.map = L.map('mappa-leaflet').setView(ITALY_CENTER, ITALY_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 19
    }).addTo(this.map);

    setTimeout(() => this.map?.invalidateSize(), 0);
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = null;
  }
}
