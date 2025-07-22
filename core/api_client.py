# core/api_client.py

import requests
import json
from django.conf import settings
from datetime import datetime, timedelta

class NsureCargoAPIClient:
    def __init__(self):
        self.api_home = getattr(settings, 'NSURE_API_HOME', None)
        self.api_key = getattr(settings, 'NSURE_API_KEY', None)
        self.username = getattr(settings, 'NSURE_USERNAME', None)
        self.password = getattr(settings, 'NSURE_PASSWORD', None)
        self._api_token = None

        if not all([self.api_home, self.api_key, self.username, self.password]):
            raise ValueError("NSure API credentials are not fully configured in settings.py")

    def _get_api_token(self):
        if self._api_token:
            return self._api_token

        login_url = f"{self.api_home}/login"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-NS-API-Key': self.api_key,
        }
        payload = {
            'username': self.username,
            'password': self.password
        }
        try:
            response = requests.post(login_url, headers=headers, json=payload)
            response.raise_for_status()
            self._api_token = response.json().get('token')
            if not self._api_token:
                raise Exception("No se obtuvo el token de la API de NSure Cargo.")
            return self._api_token
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener el token de NSure Cargo: {e}")
            raise

    def _make_request(self, method, endpoint, params=None, json_data=None):
        token = self._get_api_token()
        url = f"{self.api_home}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-NS-API-Key': self.api_key,
            'X-NS-API-Token': token,
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=json_data, params=params)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud a la API de NSure Cargo: {e}")
            raise

    def create_declaration(self, external_id=None, departure_date=None):
        """
        Crea una declaración de carga mínima en NSure Cargo.
        Necesitamos una declaración para usar los endpoints de busqueda de vessels/countries.
        """
        endpoint = "/declarations/cargo/shipments"
        
        if departure_date is None:
            departure_date = datetime.now().isoformat(sep=' ', timespec='seconds')
        else:
            departure_date = departure_date.isoformat(sep=' ', timespec='seconds')

        # Genera un externalId único si no se proporciona
        test_external_id = external_id if external_id else f"test_declaration_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # Payload con campos mínimos requeridos según la documentación
        # Ajusta estos valores según tus necesidades o los valores que acepte la API
        payload = {
            "assuredId": "NS-ASSURED-001",  # Ejemplo: ID de un asegurado de prueba
            "policyId": "NS-POLICY-001",    # Ejemplo: ID de una póliza de prueba
            "departureDate": departure_date,
            "currency": "USD",              # Ejemplo: Moneda
            "externalId": test_external_id,
            "origin": {
                "countryId": "CL",          # Ejemplo: Chile
                "countryCode": "CL",
                "countryName": "Chile"
            },
            "destination": {
                "countryId": "US",          # Ejemplo: Estados Unidos
                "countryCode": "US",
                "countryName": "United States"
            },
            "cargo": [
                {
                    "typeId": "GENERAL_CARGO", # Ejemplo: Tipo de carga general
                    "typeName": "General Cargo",
                    "amount": 1,
                    "unit": "Piece",
                    "value": 1000.00          # Ejemplo: Valor asegurado
                }
            ],
            "shipmentMethod": "Ocean"       # Ejemplo: Método de envío (Ocean, Air, Road)
        }
        
        return self._make_request('POST', endpoint, json_data=payload)

    def search_vessels(self, declaration_id_or_external_id, term, skip=0, limit=10):
        if "external-id=" in declaration_id_or_external_id:
            declaration_segment = declaration_id_or_external_id
        else:
            declaration_segment = declaration_id_or_external_id

        endpoint = f"/declarations/cargo/shipments/default/{declaration_segment}/vessels"
        params = {
            'term': term,
            'skip': skip,
            'limit': limit
        }
        return self._make_request('GET', endpoint, params=params)

    def list_countries(self, declaration_id_or_external_id):
        if "external-id=" in declaration_id_or_external_id:
            declaration_segment = declaration_id_or_external_id
        else:
            declaration_segment = declaration_id_or_external_id

        endpoint = f"/declarations/cargo/shipments/default/{declaration_segment}/countries"
        return self._make_request('GET', endpoint)

nsure_api = NsureCargoAPIClient()