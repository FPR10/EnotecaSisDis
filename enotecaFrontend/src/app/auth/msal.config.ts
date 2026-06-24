import { BrowserCacheLocation, InteractionType, IPublicClientApplication, LogLevel, PublicClientApplication } from '@azure/msal-browser';
import { MsalGuardConfiguration, MsalInterceptorConfiguration, ProtectedResourceScopes } from '@azure/msal-angular';
import { environment } from '../../environments/environment';

/**
 * Scope richiesto per chiamare il nostro backend (audience = client id dell'app registration).
 * Quando client e risorsa coincidono (l'app richiede un token per se stessa, come in questo caso),
 * Azure AD richiede l'identificatore della risorsa in forma GUID nudo, non con il prefisso "api://"
 * (altrimenti risponde AADSTS90009).
 */
const API_SCOPE = `${environment.msal.clientId}/access_as_user`;

export function MSALInstanceFactory(): IPublicClientApplication {
  return new PublicClientApplication({
    auth: {
      clientId: environment.msal.clientId,
      authority: `https://login.microsoftonline.com/${environment.msal.tenantId}`,
      redirectUri: environment.msal.redirectUri,
      postLogoutRedirectUri: '/'
    },
    cache: {
      cacheLocation: BrowserCacheLocation.LocalStorage
    },
    system: {
      loggerOptions: {
        loggerCallback: () => {},
        logLevel: LogLevel.Warning,
        piiLoggingEnabled: false
      }
    }
  });
}

export function MSALGuardConfigFactory(): MsalGuardConfiguration {
  return {
    interactionType: InteractionType.Redirect,
    authRequest: {
      scopes: ['User.Read']
    }
  };
}

/**
 * Mappa delle risorse protette: MsalInterceptor allega l'header "Authorization: Bearer <token>"
 * solo sulle scritture (POST/PUT/DELETE) verso /wines, che sul backend richiedono ruolo admin.
 * Le GET di consultazione catalogo restano pubbliche: niente token, anche se l'utente è loggato,
 * altrimenti un'acquisizione silente del token fallita romperebbe pagine che non ne hanno bisogno.
 */
export function MSALInterceptorConfigFactory(): MsalInterceptorConfiguration {
  const scrittureProtette: ProtectedResourceScopes[] = [
    { httpMethod: 'POST', scopes: [API_SCOPE] },
    { httpMethod: 'PUT', scopes: [API_SCOPE] },
    { httpMethod: 'DELETE', scopes: [API_SCOPE] },
  ];

  const protectedResourceMap = new Map<string, Array<string | ProtectedResourceScopes> | null>();
  protectedResourceMap.set(`${environment.apiBaseUrl}/wines*`, scrittureProtette);

  return {
    interactionType: InteractionType.Redirect,
    protectedResourceMap
  };
}

export function initializeMsal(msalInstance: IPublicClientApplication): () => Promise<void> {
  return () =>
    msalInstance.initialize().then(() =>
      msalInstance.handleRedirectPromise().then(result => {
        if (result?.account) {
          msalInstance.setActiveAccount(result.account);
          return;
        }
        const accounts = msalInstance.getAllAccounts();
        if (accounts.length > 0) {
          msalInstance.setActiveAccount(accounts[0]);
        }
      })
    );
}
