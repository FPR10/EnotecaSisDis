import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HomeComponent } from './home/home.component';
import { ContactComponent } from './contact/contact.component';
import { MappaComponent } from './mappa/mappa.component';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter([
      { path: '', component: HomeComponent },
      { path: 'contact', component: ContactComponent },
      { path: 'mappa', component: MappaComponent },
    ]),
    provideHttpClient(),
  ]
};
