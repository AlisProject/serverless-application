import os
import json
import requests
import settings
from jsonschema import validate
from parameter_util import ParameterUtil
from authlete_util import AuthleteUtil
from lambda_base import LambdaBase


class ApplicationShow(LambdaBase):
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

    def exec_main_proc(self):
        try:
            response = requests.get(
                settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + str(self.params['client_id']),
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )
        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))

        AuthleteUtil.verify_valid_response(response, request_client_id=self.params['client_id'])

        response_dict = json.loads(response.text)
        return_body_dict = {
            'clientName': response_dict['clientName'],
            'description': response_dict.get('description')
        }

        return {
            'statusCode': 200,
            'body': json.dumps(return_body_dict)
        }
