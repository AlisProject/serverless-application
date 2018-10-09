import re
import json
import settings

from urllib.parse import parse_qsl
from requests_oauthlib import OAuth1Session
from exceptions import TwitterOauthError


class TwitterUtil:
    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def get_user_info(self, oauth_token, oauth_verifier):
        response = self.__get_access_token(
            oauth_token=oauth_token,
            oauth_verifier=oauth_verifier
        )

        if response.status_code is not 200:
            raise TwitterOauthError(
                endpoint=settings.TWITTER_API_ACCESS_TOKEN_URL,
                status_code=response.status_code,
                message=response.text
            )

        access_token = self.__parse_api_response(
            response=response
        )
        cognito_user_id = self.__generate_user_id(access_token['user_id'])

        twitter = OAuth1Session(
            self.consumer_key,
            self.consumer_secret,
            access_token['oauth_token'],
            access_token['oauth_token_secret'],
        )

        response = twitter.get(
            settings.TWITTER_API_VERIFY_CREDENTIALS_URL + '?include_email=true'
        )

        if response.status_code is not 200:
            raise TwitterOauthError(
                endpoint=settings.TWITTER_API_VERIFY_CREDENTIALS_URL,
                status_code=response.status_code,
                message=response.text
            )

        user_info = json.loads(response.text)
        return {
            'user_id': cognito_user_id,
            'email': self.__get_email(user_info, cognito_user_id),
            'display_name': self.__get_display_name(user_info),
            'icon_image_url': self.__get_icon_image_url(user_info)
        }

    def generate_auth_url(self, callback_url):
        twitter = OAuth1Session(
            self.consumer_key,
            self.consumer_secret
        )
        response = twitter.post(
            settings.TWITTER_API_REQUEST_TOKEN_URL,
            params={'oauth_callback': callback_url}
        )

        if response.status_code is not 200:
            raise TwitterOauthError(
                endpoint=settings.TWITTER_API_REQUEST_TOKEN_URL,
                status_code=response.status_code,
                message=response.text
            )

        response_body = self.__parse_api_response(
            response=response
        )
        return '%s?oauth_token=%s' \
            % (settings.TWITTER_API_AUTHENTICATE_URL, response_body['oauth_token'])

    def __parse_api_response(self, response):
        return dict(parse_qsl(response.content.decode('utf-8')))

    def __generate_user_id(self, twitter_user_id):
        return settings.TWITTER_USERNAME_PREFIX + twitter_user_id

    def __get_access_token(self, oauth_token, oauth_verifier):
        twitter = OAuth1Session(
            self.consumer_key,
            self.consumer_secret,
            oauth_token,
            oauth_verifier
        )

        return twitter.post(
            settings.TWITTER_API_ACCESS_TOKEN_URL,
            params={'oauth_verifier': oauth_verifier}
        )

    def __get_icon_image_url(self, user_info):
        icon_image_url = user_info.get('profile_image_url_https')
        if re.search(r'/default_profile_images/', icon_image_url):
            return None

        return icon_image_url.replace('_normal', '')

    def __get_display_name(self, user_info):
        return user_info.get('screen_name')

    def __get_email(self, user_info, cognito_user_id):
        email = user_info.get('email')
        if email is None or email == '':
            email = cognito_user_id + '@' + settings.FAKE_USER_EMAIL_DOMAIN

        return email
