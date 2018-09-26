import json
import os
import settings

from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase
from urllib.parse import parse_qsl
from requests_oauthlib import OAuth1Session


class LoginTwitterAuthorizationUrl(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        twitter = OAuth1Session(
            os.environ['TWITTER_CONSUMER_KEY'],
            os.environ['TWITTER_CONSUMER_SECRET']
        )
        response = twitter.post(
            settings.TWITTER_API_REQUEST_TOKEN_URL,
            params={'oauth_callback': os.environ['TWITTER_OAUTH_CALLBACK_URL']}
        )

        request_token = dict(parse_qsl(response.content.decode('utf-8')))
        authenticate_endpoint = '%s?oauth_token=%s' \
            % (settings.TWITTER_API_AUTHENTICATE_URL, request_token['oauth_token'])

        return {
            'statusCode': 200,
            'body': json.dumps({'url': authenticate_endpoint}, cls=DecimalEncoder)
        }
