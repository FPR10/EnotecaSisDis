import * as L from 'leaflet';

/** Centroide approssimativo di ciascuna regione italiana, usato per posizionare i vini in mappa. */
export const REGION_COORDINATES: Record<string, L.LatLngTuple> = {
  'Abruzzo': [42.35, 13.4],
  'Basilicata': [40.6, 16.05],
  'Calabria': [39.1, 16.3],
  'Campania': [40.83, 14.75],
  'Emilia-Romagna': [44.5, 11.3],
  'Friuli-Venezia Giulia': [46.05, 13.2],
  'Lazio': [41.9, 12.6],
  'Liguria': [44.3, 8.9],
  'Lombardia': [45.5, 9.8],
  'Marche': [43.3, 13.2],
  'Molise': [41.6, 14.3],
  'Piemonte': [45.05, 7.7],
  'Puglia': [41.1, 16.6],
  'Sardegna': [40.1, 9.0],
  'Sicilia': [37.6, 14.0],
  'Toscana': [43.4, 11.1],
  'Trentino-Alto Adige': [46.4, 11.2],
  'Umbria': [43.0, 12.5],
  'Valle d\'Aosta': [45.7, 7.3],
  'Veneto': [45.5, 11.9],
};
