# -*- coding: utf-8 -*-
import os
import secrets
import settings
import json
from lambda_base import LambdaBase


class SignUpLineAuthorizeUrl(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        redirect_url = '&redirect_uri=' + os.environ['LINE_REDIRECT_URI']
        state_and_scope = '&state=' + self.__generate_state() + settings.LINE_REQUEST_SCOPE
        url = settings.LINE_AUTHORIZE_URL + os.environ['LINE_CHANNEL_ID'] + redirect_url + state_and_scope

        return {
            'statusCode': 200,
            'body': json.dumps({
                'callback_url': url
            })
        }

    @staticmethod
    def __generate_state():
        return secrets.token_hex(4)
