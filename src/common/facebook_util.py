import json
import settings
import requests
import hmac
import hashlib

from nonce_util import NonceUtil
from botocore.exceptions import ClientError
from exceptions import FacebookOauthError
from exceptions import FacebookVerifyException


class FacebookUtil:
    def __init__(self, app_id, app_secret, callback_url, app_token):
        self.app_id = app_id
        self.app_secret = app_secret
        self.callback_url = callback_url
        self.app_token = app_token

    def verify_state_nonce(self, dynamodb, state):
        nonce_checked = NonceUtil.verify(
            dynamodb=dynamodb,
            nonce=state,
            provider='facebook',
            type='state'
        )

        if nonce_checked is False:
            raise FacebookVerifyException(state + ' was invalid since it may be expired')
        return True

    def remove_postfix_str_from_state_token(self, state):
        return state.rstrip('#_=_')

    def get_authorization_url(self, dynamodb):
        try:
            state = NonceUtil.generate(
                dynamodb=dynamodb,
                expiration_minites=settings.FACEBOOK_NONCE_EXPIRATION_MINUTES,
                provider='facebook',
                type='state',
                length=settings.FACEBOOK_NONCE_LENGTH
            )
        except (ClientError) as e:
            raise e

        authorization_endpoint = \
            settings.FACEBOOK_API_AUTHENTICATE_URL + \
            '?client_id=' + self.app_id + \
            '&redirect_uri=' + self.callback_url + \
            '&scope=' + settings.FACEBOOK_LOGIN_REQUEST_SCOPE + \
            '&state='+state

        return authorization_endpoint

    def get_access_token(self, code):
        response = requests.get(
            settings.FACEBOOK_API_ACCESSTOKEN_URL +
            '?client_id=' + self.app_id +
            '&client_secret=' + self.app_secret +
            '&redirect_uri=' + self.callback_url +
            '&code=' + code
        )

        if response.status_code != 200:
            raise FacebookOauthError(
                endpoint=settings.FACEBOOK_API_ACCESSTOKEN_URL,
                status_code=response.status_code,
                message=response.text
            )
        token = json.loads(response.text)
        return token['access_token']

    def get_user_info(self, access_token):
        response = requests.get(
            settings.FACEBOOK_API_USERINFO_URL +
            '?access_token=' + access_token +
            '&fields=id,email&appsecret_proof=' +
            self.__get_appsecret_proof(access_token)
        )
        if response.status_code != 200:
            raise FacebookOauthError(
                endpoint=settings.FACEBOOK_API_USERINFO_URL,
                status_code=response.status_code,
                message=response.text
            )

        user_info = json.loads(response.text)

        verified = self.__verify_access_token(
            access_token=access_token,
            user_id=user_info['id']
        )

        if verified is False:
            raise FacebookVerifyException('this access_token is invalid')

        cognito_user_id = self.__generate_user_id(
            facebook_user_id=user_info['id']
        )
        email = self.__get_email(
            user_info=user_info,
            cognito_user_id=cognito_user_id
        )
        return {
            'user_id': cognito_user_id,
            'email': email
        }

    def __verify_access_token(self, access_token, user_id):
        response = requests.get(
            settings.FACEBOOK_API_DEBUG_URL +
            '?access_token=' + self.app_token +
            '&input_token=' + access_token +
            '&appsecret_proof=' + self.__get_appsecret_proof(access_token)
        )

        if response.status_code != 200:
            raise FacebookOauthError(
                endpoint=settings.FACEBOOK_API_DEBUG_URL,
                status_code=response.status_code,
                message=response.text
            )
        data = json.loads(response.text)
        if data['data']['app_id'] != self.app_id or \
           data['data']['user_id'] != user_id:
            return False

        return True

    def __get_appsecret_proof(self, access_token):
        return hmac.new(
            self.app_secret.encode('utf-8'),
            access_token.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def __generate_user_id(self, facebook_user_id):
        return settings.FACEBOOK_USERNAME_PREFIX + facebook_user_id

    def __get_email(self, user_info, cognito_user_id):
        email = user_info.get('email')
        if email is None:
            email = cognito_user_id + '@' + settings.FAKE_USER_EMAIL_DOMAIN
        return email
