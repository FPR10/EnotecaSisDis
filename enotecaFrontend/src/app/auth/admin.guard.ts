import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { MsalService } from '@azure/msal-angular';
import { environment } from '../../environments/environment';

export const adminGuard: CanActivateFn = () => {
  const msal = inject(MsalService);
  const router = inject(Router);

  const account = msal.instance.getActiveAccount();
  const roles = (account?.idTokenClaims?.['roles'] as string[]) ?? [];

  if (!roles.includes(environment.msal.adminAppRole)) {
    return router.createUrlTree(['/accesso-negato']);
  }

  return true;
};
