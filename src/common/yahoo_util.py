import json
import settings
import requests
from nonce_util import NonceUtil
from exceptions import YahooOauthError
from botocore.exceptions import ClientError


class YahooUtil:
    def __init__(self, client_id, secret):
        self.client_id = client_id
        self.secret = secret

    def get_authorization_url(self, dynamodb, callback_url):
        try:
            endpoints = self._get_endpoins()
            nonce = NonceUtil.generate(
                dynamodb=dynamodb,
                expiration_minites=settings.YAHOO_NONCE_EXPIRATION_MINITES,
                provider='yahoo',
                type='nonce',
                length=settings.YAHOO_NONCE_LENGTH
            )
            state = NonceUtil.generate(
                dynamodb=dynamodb,
                expiration_minites=settings.YAHOO_NONCE_EXPIRATION_MINITES,
                provider='yahoo',
                type='state',
                length=settings.YAHOO_NONCE_LENGTH
            )
        except (ClientError, YahooOauthError) as e:
            raise e
        authorization_endpoint = \
            endpoints['authorization_endpoint'] + \
            '?response_type=' + settings.YAHOO_LOGIN_RESPONSE_TYPE + \
            '&client_id=' + self.client_id + \
            '&scope=' + settings.YAHOO_LOGIN_REQUEST_SCOPE + \
            '&redirect_uri=' + callback_url + \
            '&nonce='+nonce+'&state='+state

        return authorization_endpoint

    def _get_endpoins(self):
        response = requests.get(settings.YAHOO_API_WELL_KNOWN_URL)

        if response.status_code is not 200:
            raise YahooOauthError(
                endpoint=settings.YAHOO_API_WELL_KNOWN_URL,
                status_code=response.status_code,
                message=response.text
            )
        return json.loads(response.text)
