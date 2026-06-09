import { Injectable } from '@angular/core';
import { Wine } from '../models/wine.model';

@Injectable({ providedIn: 'root' })
export class WineService {

  //Vini presenti nella sezione sezione "Consigliati"
  private wines: Wine[] = [
    {
      id: '1',
      name: 'Barolo Riserva 2018',
      producer: 'Marchesi di Barolo',
      year: 2018,
      winery: 'Marchesi di Barolo',
      denomination: 'DOCG',
      region: 'Piemonte',
      description: 'Grande rosso piemontese, strutturato e longevo.',
      price: 65,
      available: true,
      type: 'Rosso',
      featured: true
    },
    {
      id: '2',
      name: 'Greco di Tufo 2022',
      producer: 'Feudi di San Gregorio',
      year: 2022,
      winery: 'Feudi di San Gregorio',
      denomination: 'DOCG',
      region: 'Campania',
      description: 'Bianco campano floreale e minerale.',
      price: 18,
      available: true,
      type: 'Bianco',
      featured: true
    },
    {
      id: '3',
      name: 'Franciacorta Brut DOC',
      producer: 'Bellavista',
      year: undefined,
      winery: 'Bellavista',
      denomination: 'DOCG',
      region: 'Lombardia',
      description: 'Bollicina lombarda elegante e persistente.',
      price: 28,
      available: true,
      type: 'Bollicine',
      featured: true
    },
    {
      id: '4',
      name: 'Brunello di Montalcino',
      producer: 'Biondi-Santi',
      year: 2019,
      winery: 'Biondi-Santi',
      denomination: 'DOCG',
      region: 'Toscana',
      description: 'Icona toscana, eleganza e longevità assoluta.',
      price: 120,
      available: true,
      type: 'Rosso',
      featured: true
    },
    {
      id: '5',
      name: "Cerasuolo d'Abruzzo",
      producer: 'Valentini',
      year: 2022,
      winery: 'Valentini',
      denomination: 'DOC',
      region: 'Abruzzo',
      description: 'Rosato abruzzese dal colore ciliegia vivace.',
      price: 22,
      available: true,
      type: 'Rosato',
      featured: true
    },
    {
      id: '6',
      name: 'Cirò Bianco DOC 2023',
      producer: 'Librandi',
      year: 2023,
      winery: 'Librandi',
      denomination: 'DOC',
      region: 'Calabria',
      description: 'Vino bianco calabrese fresco e sapido.',
      price: 12,
      available: true,
      type: 'Bianco',
      featured: true
    }
  ];

  getAll(): Wine[] {
    return this.wines;
  }

  getFeatured(): Wine[] {
    return this.wines.filter(w => w.featured);
  }

  getByType(type: string): Wine[] {
    return this.wines.filter(w => w.type === type);
  }

  getByRegion(region: string): Wine[] {
    return this.wines.filter(w => w.region === region);
  }

  search(query: string): Wine[] {
    const q = query.toLowerCase();
    return this.wines.filter(w =>
      w.name.toLowerCase().includes(q) ||
      w.producer.toLowerCase().includes(q) ||
      w.region.toLowerCase().includes(q) ||
      (w.denomination?.toLowerCase().includes(q) ?? false)
    );
  }

  searchByField(field: string, query: string): Wine[] {
    const q = query.toLowerCase();
    switch (field) {
      case 'tipo':
        return this.wines.filter(w => w.type.toLowerCase() === q);
      case 'nome':
        return this.wines.filter(w =>
          w.name.toLowerCase().includes(q) || w.producer.toLowerCase().includes(q)
        );
      case 'regione':
        return this.wines.filter(w => w.region.toLowerCase().includes(q));
      case 'denominazione':
        return this.wines.filter(w => w.denomination?.toLowerCase().includes(q) ?? false);
      default:
        return this.search(query);
    }
  }

  add(wine: Wine): void {
    this.wines.push(wine);
  }
}
