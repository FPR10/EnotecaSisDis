export type WineType = 'Rosso' | 'Bianco' | 'Rosato' | 'Bollicine';

export interface Wine {
  id: string;
  name: string;
  producer: string;
  year?: number;
  winery: string;
  denomination?: string;
  grapeVariety?: string;
  region: string;
  country?: string;
  description?: string;
  price?: number;
  quantity?: number;
  available: boolean;
  type: WineType;
  imageUrl?: string;
  featured?: boolean;
  /** Punteggio di popolarità del vino (1-5), usato ad es. per le classifiche regionali in mappa. */
  popularity?: number;
}

export interface CaratteristicheOrganolettiche {
  colore?: string;
  profumo?: string[];
  gusto?: string;
}

/** Vino come restituito dal backend (WineOut) — campi in italiano, a differenza di Wine usato nei mockup. */
export interface WineApi {
  id: string;
  nome: string;
  produttore: string;
  azienda_vinicola: string;
  regione: string;
  tipo: 'rosso' | 'bianco' | 'rosato' | 'bollicine';
  disponibile: boolean;
  dati_creazione: string;
  dati_aggiornamento: string;
  annata?: number;
  denominazione?: string;
  descrizione?: string;
  prezzo?: number;
  immagine_etichetta?: string;
  vitigno?: string;
  caratteristiche_organolettiche?: CaratteristicheOrganolettiche;
  popolarita?: number;
  scorte?: number;
}

const WINE_TYPE_MAP: Record<WineApi['tipo'], WineType> = {
  rosso: 'Rosso',
  bianco: 'Bianco',
  rosato: 'Rosato',
  bollicine: 'Bollicine',
};

/** Converte un vino del backend (campi italiani) nel modello Wine usato dai componenti mockup. */
export function wineFromApi(api: WineApi): Wine {
  return {
    id: api.id,
    name: api.nome,
    producer: api.produttore,
    year: api.annata,
    winery: api.azienda_vinicola,
    denomination: api.denominazione,
    grapeVariety: api.vitigno,
    region: api.regione,
    description: api.descrizione,
    price: api.prezzo,
    quantity: api.scorte,
    available: api.disponibile,
    type: WINE_TYPE_MAP[api.tipo],
    imageUrl: api.immagine_etichetta,
    popularity: api.popolarita,
  };
}
