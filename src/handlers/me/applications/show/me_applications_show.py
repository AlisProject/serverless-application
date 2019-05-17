import os

import requests
from jsonschema import validate

import settings
from authlete_util import AuthleteUtil
from lambda_base import LambdaBase
from no_permission_error import NoPermissionError
from parameter_util import ParameterUtil


class MeApplicationShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'client_id': settings.parameters['oauth_client']['client_id']
            }
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema())

        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        if not AuthleteUtil.is_accessible_client(self.params['client_id'], user_id):
            raise NoPermissionError('No permission on this resource')

    def exec_main_proc(self):
        try:
            response = requests.get(
                settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + str(self.params['client_id']),
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )
        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))

        AuthleteUtil.verify_valid_response(response, request_client_id=self.params['client_id'])

        return {
            'statusCode': 200,
            'body': response.text
        }
