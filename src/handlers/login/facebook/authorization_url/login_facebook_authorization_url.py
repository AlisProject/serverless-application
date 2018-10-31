import os
import logging
import traceback
from lambda_base import LambdaBase
from facebook_util import FacebookUtil
from exceptions import FacebookOauthError
from botocore.exceptions import ClientError
from response_builder import ResponseBuilder


class LoginFacebookAuthorizationUrl(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        facebook = FacebookUtil(
           app_id=os.environ['FACEBOOK_APP_ID'],
           app_secret=os.environ['FACEBOOK_APP_SECRET']
        )
        try:
            authentication_url = facebook.get_authorization_url(
              dynamodb=self.dynamodb,
              callback_url=os.environ['FACEBOOK_OAUTH_CALLBACK_URL']
            )
        except (ClientError, FacebookOauthError) as e:
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
