import { BrowserCacheLocation, InteractionType, IPublicClientApplication, LogLevel, PublicClientApplication } from '@azure/msal-browser';
import { MsalGuardConfiguration } from '@azure/msal-angular';
import { environment } from '../../environments/environment';

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
