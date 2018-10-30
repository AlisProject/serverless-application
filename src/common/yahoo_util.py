import json
import settings
import requests
import time
import jwt
import hashlib
import base64
from nonce_util import NonceUtil
from exceptions import YahooOauthError
from exceptions import YahooVerifyException
from botocore.exceptions import ClientError

from jwt.contrib.algorithms.pycrypto import RSAAlgorithm
jwt.register_algorithm('RS256', RSAAlgorithm(RSAAlgorithm.SHA256))


class YahooUtil:
    def __init__(self, client_id, secret):
        self.client_id = client_id
        self.secret = secret
        self.endpoints = self.__get_endpoins()

    def get_authorization_url(self, dynamodb, callback_url):
        try:
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
            self.endpoints['authorization_endpoint'] + \
            '?response_type=code' + \
            '&client_id=' + self.client_id + \
            '&scope=' + settings.YAHOO_LOGIN_REQUEST_SCOPE + \
            '&redirect_uri=' + callback_url + \
            '&nonce='+nonce+'&state='+state

        return authorization_endpoint

    def verify_state_nonce(self, dynamodb, state):
        nonce_checked = NonceUtil.verify(
            dynamodb=dynamodb,
            nonce=state,
            provider='yahoo',
            type='state'
        )

        if nonce_checked is False:
            raise YahooVerifyException(state + ' was invalid since it may be expired')
        return True

    def get_access_token(self, code, callback_url):
        basicauth_str = self.client_id + ':' + self.secret
        basicauth = base64.b64encode(basicauth_str.encode('utf-8'))

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + basicauth.decode('UTF-8')
        }

        # アクセストークンの取得
        response = requests.post(
            self.endpoints['token_endpoint'],
            headers=headers,
            data='grant_type=authorization_code&redirect_uri=' + callback_url + '&code=' + code
        )
        if response.status_code is not 200:
            raise YahooOauthError(
                endpoint=self.endpoints['token_endpoint'],
                status_code=response.status_code,
                message=response.text
            )
        return json.loads(response.text)

    def verify_access_token(self, dynamodb, access_token, id_token):
        # 以下のコメントはhttps://developer.yahoo.co.jp/yconnect/v2/id_token.htmlの検証手順番号
        try:
            start_time = time.time()
            header = jwt.get_unverified_header(id_token)
            response = requests.get(
                settings.YAHOO_API_PUBLIC_KEY_URL
            )
            if response.status_code is not 200:
                raise YahooOauthError(
                    endpoint=settings.YAHOO_API_WELL_KNOWN_URL,
                    status_code=response.status_code,
                    message=response.text
                )
            public_keys = json.loads(response.text)

            # 6,7,8の検証
            decoded_data = jwt.decode(
                id_token,
                key=public_keys.get(header['kid']).encode('utf-8'),
                issuer=self.endpoints['issuer'],
                audience=self.client_id,
                algorithms='RS256')

            nonce_checked = NonceUtil.verify(
                dynamodb=dynamodb,
                nonce=decoded_data['nonce'],
                provider='yahoo',
                type='nonce'
            )

            # 9の検証
            if nonce_checked is False:
                raise YahooVerifyException('id token was invalid since nonce was invalid')

            # 10の検証
            token_hash = hashlib.sha256(access_token.encode('utf-8')).digest()
            at_hash = base64.urlsafe_b64encode(
                token_hash[:int(len(token_hash) / 2)]
            )
            if decoded_data['at_hash'] != at_hash.decode().rstrip('='):
                raise YahooVerifyException('accesstoken was invalid since at_hash did not match')

            # 12の検証
            if start_time >= decoded_data['exp']:
                raise YahooVerifyException('id token was invalid since start_time was less than exp')
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            ClientError,
            YahooVerifyException
        ) as e:
            raise e

        return True

    def get_user_info(self, access_token):
        response = requests.get(
            self.endpoints['userinfo_endpoint'] + '?access_token=' + access_token
        )
        if response.status_code is not 200:
            raise YahooOauthError(
                endpoint=self.endpoints['userinfo_endpoint'],
                status_code=response.status_code,
                message=response.text
            )
        profile = json.loads(response.text)
        cognito_user_id = self.__generate_user_id(
            yahoo_user_id=profile['sub']
        )

        return {
            'user_id': cognito_user_id,
            'email': profile['email']
        }

    def __get_endpoins(self):
        response = requests.get(settings.YAHOO_API_WELL_KNOWN_URL)

        if response.status_code is not 200:
            raise YahooOauthError(
                endpoint=settings.YAHOO_API_WELL_KNOWN_URL,
                status_code=response.status_code,
                message=response.text
            )
        return json.loads(response.text)

    def __generate_user_id(self, yahoo_user_id):
        return settings.YAHOO_USERNAME_PREFIX + yahoo_user_id
