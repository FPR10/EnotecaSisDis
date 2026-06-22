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
}
