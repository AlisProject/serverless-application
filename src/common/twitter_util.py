import json
import os
import settings

from urllib.parse import parse_qsl
from requests_oauthlib import OAuth1Session
from exceptions import TwitterOauthError


class TwitterUtil:
    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

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
            raise TwitterOauthError(response.text)

        response_body = self.parse_api_response(
            response=response
        )
        return '%s?oauth_token=%s' \
            % (settings.TWITTER_API_AUTHENTICATE_URL, response_body['oauth_token'])

    def parse_api_response(self, response):
        return dict(parse_qsl(response.content.decode('utf-8')))

    def get_authentication_url(self, oauth_token):
        return '%s?oauth_token=%s' \
            % (settings.TWITTER_API_AUTHENTICATE_URL, oauth_token)

    def generate_user_id(self, twitter_user_id):
        return settings.TWITTER_USERNAME_PREFIX + twitter_user_id
