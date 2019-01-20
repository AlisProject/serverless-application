import os

import requests

import settings
from authlete_util import AuthleteUtil
from lambda_base import LambdaBase


class MeApplicationIndex(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        index_params = {'developer': self.event['requestContext']['authorizer']['claims']['cognito:username']}

        try:
            response = requests.get(
                settings.AUTHLETE_CLIENT_ENDPOINT + '/get/list',
                params=index_params,
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )

        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))

        AuthleteUtil.verify_valid_response(response)

        return {
            'statusCode': 200,
            'body': response.text
        }
