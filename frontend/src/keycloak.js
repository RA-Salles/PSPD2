import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: 'https://kiriland.unb.br/keycloak',
  realm: 'grupo02',
  clientId: 'flask-backend'
});

export default keycloak;