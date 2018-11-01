import os
import logging
import traceback
from lambda_base import LambdaBase
from yahoo_util import YahooUtil
from exceptions import YahooOauthError
from botocore.exceptions import ClientError
from response_builder import ResponseBuilder


class LoginYahooAuthorizationUrl(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        yahoo = YahooUtil(
           client_id=os.environ['YAHOO_CLIENT_ID'],
           secret=os.environ['YAHOO_SECRET'],
           callback_url=os.environ['YAHOO_OAUTH_CALLBACK_URL']
        )
        try:
            authentication_url = yahoo.get_authorization_url(
              dynamodb=self.dynamodb
            )
        except (ClientError, YahooOauthError) as e:
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
