import { APP_INITIALIZER, ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import {
  MSAL_GUARD_CONFIG,
  MSAL_INSTANCE,
  MSAL_INTERCEPTOR_CONFIG,
  MsalBroadcastService,
  MsalGuard,
  MsalInterceptor,
  MsalService
} from '@azure/msal-angular';
import { HomeComponent } from './home/home.component';
import { ContactComponent } from './contact/contact.component';
import { MappaComponent } from './mappa/mappa.component';
import { CatalogoViniComponent } from './catalogo-vini/catalogo-vini.component';
import { AggiungiVinoComponent } from './aggiungiVino/aggiungi-vino.component';
import { GestisciViniComponent } from './gestisciVini/gestisci-vini.component';
import { AccessDeniedComponent } from './auth/access-denied.component';
import { adminGuard } from './auth/admin.guard';
import { initializeMsal, MSALGuardConfigFactory, MSALInstanceFactory, MSALInterceptorConfigFactory } from './auth/msal.config';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter([
      { path: '', component: HomeComponent },
      { path: 'catalogo', component: CatalogoViniComponent },
      { path: 'contact', component: ContactComponent },
      { path: 'mappa', component: MappaComponent },
      { path: 'aggiungi-vino', component: AggiungiVinoComponent, canActivate: [MsalGuard, adminGuard] },
      { path: 'gestisci-vini', component: GestisciViniComponent, canActivate: [MsalGuard, adminGuard] },
      { path: 'accesso-negato', component: AccessDeniedComponent },
    ]),
    provideHttpClient(withInterceptorsFromDi()),
    { provide: MSAL_INSTANCE, useFactory: MSALInstanceFactory },
    { provide: MSAL_GUARD_CONFIG, useFactory: MSALGuardConfigFactory },
    { provide: MSAL_INTERCEPTOR_CONFIG, useFactory: MSALInterceptorConfigFactory },
    { provide: HTTP_INTERCEPTORS, useClass: MsalInterceptor, multi: true },
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
