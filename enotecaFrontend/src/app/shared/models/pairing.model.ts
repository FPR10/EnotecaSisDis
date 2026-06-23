/** Modelli per l'abbinamento cibo-vino (POST /pairing/abbinamento). Rispecchiano i DTO del backend. */

import { WineApi } from './wine.model';

export interface VinoSuggerito {
  wine: WineApi;
  motivazione: string;
}

export interface AbbinamentoOut {
  cibo: string;
  suggerimenti: VinoSuggerito[];
}
