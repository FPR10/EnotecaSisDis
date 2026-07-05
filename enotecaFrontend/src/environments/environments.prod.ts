export const environment = {
  production: true,
  apiBaseUrl: 'https://enoteca-backend.azurewebsites.net/api/v1',
  msal: {
    clientId: 'b91c6907-f07c-490f-a473-b28e640432f0',
    tenantId: '92c56a5a-bd4a-434d-9c0e-e03f070c220f',
    redirectUri: 'http://localhost:4200',  //frontend rimane su localhost
    adminAppRole: 'Enoteca.Admin'
  }
};