import os
import logging
import traceback

from lambda_base import LambdaBase
from twitter_util import TwitterUtil
from exceptions import TwitterOauthError
from response_builder import ResponseBuilder


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
            logging.info(self.event)
            logging.fatal(e)
            traceback.print_exc()
            return ResponseBuilder.response(
                status_code=500,
                body={'message': 'Internal server error'}
            )

        return ResponseBuilder.response(
            status_code=200,
            body={'url': authentication_url}
        )
