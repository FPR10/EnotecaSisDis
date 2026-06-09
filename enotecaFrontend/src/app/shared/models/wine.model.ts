export type WineType = 'Rosso' | 'Bianco' | 'Rosato' | 'Bollicine';

export interface Wine {
  id: string;
  name: string;
  producer: string;
  year?: number;
  winery: string;
  denomination?: string;
  region: string;
  description?: string;
  price?: number;
  available: boolean;
  type: WineType;
  imageUrl?: string;
  featured?: boolean;
}
