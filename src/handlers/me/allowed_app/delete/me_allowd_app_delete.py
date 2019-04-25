import os
import requests
from jsonschema import validate

import settings
from authlete_util import AuthleteUtil
from lambda_base import LambdaBase


class MeAllowdAppDelete(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'client_id': settings.parameters['oauth_client']['client_id']
            }
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        subject = self.event['requestContext']['authorizer']['claims']['cognito:username']
        url = settings.AUTHLETE_CLIENT_ENDPOINT + '/authorization/delete/' + str(self.params['client_id']) + '/' + subject
        try:
            response = requests.delete(
                url,
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )
        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))

        AuthleteUtil.verify_valid_response(response, request_client_id=self.params['client_id'])

        return {
            'statusCode': 200,
            'body': '{"result": "OK"}'
        }
