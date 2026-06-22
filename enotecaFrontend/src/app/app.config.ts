import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HomeComponent } from './home/home.component';
import { ContactComponent } from './contact/contact.component';
import { MappaComponent } from './mappa/mappa.component';
import { AggiungiVinoComponent } from './aggiungiVino/aggiungi-vino.component';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter([
      { path: '', component: HomeComponent },
      { path: 'contact', component: ContactComponent },
      { path: 'mappa', component: MappaComponent },
      { path: 'aggiungi-vino', component: AggiungiVinoComponent },
    ]),
    provideHttpClient(),
  ]
};
