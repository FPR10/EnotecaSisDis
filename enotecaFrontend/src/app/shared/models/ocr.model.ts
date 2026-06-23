/** Modello per il riconoscimento etichetta (POST /ocr/etichetta). Rispecchia il DTO del backend. */

import { WineApi } from './wine.model';

export interface OcrSearchOut {
  extracted_text: string;
  results: WineApi[];
}
