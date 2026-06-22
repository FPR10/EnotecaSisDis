import { APP_INITIALIZER, ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { MSAL_GUARD_CONFIG, MSAL_INSTANCE, MsalBroadcastService, MsalGuard, MsalService } from '@azure/msal-angular';
import { HomeComponent } from './home/home.component';
import { ContactComponent } from './contact/contact.component';
import { MappaComponent } from './mappa/mappa.component';
import { AggiungiVinoComponent } from './aggiungiVino/aggiungi-vino.component';
import { AccessDeniedComponent } from './auth/access-denied.component';
import { adminGuard } from './auth/admin.guard';
import { initializeMsal, MSALGuardConfigFactory, MSALInstanceFactory } from './auth/msal.config';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter([
      { path: '', component: HomeComponent },
      { path: 'contact', component: ContactComponent },
      { path: 'mappa', component: MappaComponent },
      { path: 'aggiungi-vino', component: AggiungiVinoComponent, canActivate: [MsalGuard, adminGuard] },
      { path: 'accesso-negato', component: AccessDeniedComponent },
    ]),
    provideHttpClient(),
    { provide: MSAL_INSTANCE, useFactory: MSALInstanceFactory },
    { provide: MSAL_GUARD_CONFIG, useFactory: MSALGuardConfigFactory },
    {
      provide: APP_INITIALIZER,
      useFactory: initializeMsal,
      deps: [MSAL_INSTANCE],
      multi: true
    },
    MsalService,
    MsalGuard,
    MsalBroadcastService,
  ]
};
