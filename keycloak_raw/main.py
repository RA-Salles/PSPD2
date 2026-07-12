"""
    this was a basic test to verify if it was possible to directly 
"""

import requests

KC_URL = "https://kiriland.unb.br/keycloak"
REALM  = "grupo02"

URL_BASE = KC_URL + '/realms/' + REALM + '/account'

another_url = 'https://kiriland.unb.br/keycloak/realms/grupo02/login-actions/authenticate?session_code=REze2z9He2uvGkPOJQ--FEUmtfdtZhlBAwPvwE8DYaE&execution=577949f2-40ed-47ec-aa9e-6a10d22a84e9&client_id=account-console&tab_id=YTscc4ws0dM&client_data=eyJydSI6Imh0dHBzOi8va2lyaWxhbmQudW5iLmJyL2tleWNsb2FrL3JlYWxtcy9ncnVwbzAyL2FjY291bnQiLCJydCI6ImNvZGUiLCJybSI6InF1ZXJ5Iiwic3QiOiIzNTJjZWE3Ny00NzQwLTQwNWUtYmY4Ni05YjhlODBiNDNhZGIifQ'

response = requests.post(another_url, data={'username': "med.cardoso", 'password':	"PseudoPEP2026!"})
print(response) # verdict -> doesn't work!
print(response.raw)