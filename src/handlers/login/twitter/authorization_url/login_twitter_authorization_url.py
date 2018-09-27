import json
import os
import settings
import logging

from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase
from requests_oauthlib import OAuth1Session
from twitter_util import TwitterUtil


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

        response_body = TwitterUtil.parse_api_response(response)
        if response.status_code is not 200:
            logging.fatal(response_body)
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({
                'url': TwitterUtil.get_authentication_url(response_body['oauth_token'])
            }, cls=DecimalEncoder)
        }
