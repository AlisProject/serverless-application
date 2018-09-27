import json
import os
import settings
import logging

from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase
from requests_oauthlib import OAuth1Session
from twitter_util import TwitterUtil
from exceptions import TwitterOauthError


class LoginTwitterAuthorizationUrl(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        twitter = TwitterUtil(
            consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
            consumer_secret=os.environ['TWITTER_CONSUMER_SECRET']
        )

        try:
            authentication_url = twitter.generate_auth_url(
                callback_url=os.environ['TWITTER_OAUTH_CALLBACK_URL']
            )
        except TwitterOauthError as e:
            logging.fatal(e)
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({
                'url': authentication_url
            }, cls=DecimalEncoder)
        }
