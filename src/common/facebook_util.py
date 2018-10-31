import settings
from nonce_util import NonceUtil
from botocore.exceptions import ClientError


class FacebookUtil:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret

    def get_authorization_url(self, dynamodb, callback_url):
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
            '&redirect_uri=' + callback_url + \
            '&scope=' + settings.FACEBOOK_LOGIN_REQUEST_SCOPE + \
            '&state='+state

        return authorization_endpoint
