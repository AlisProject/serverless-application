import os

import requests
import settings
import json
from authlete_util import AuthleteUtil
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from parameter_util import ParameterUtil


class MeAllowedApplicationsIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'start': settings.parameters['authlete_allowed_app_index_parameter'],
                'end': settings.parameters['authlete_allowed_app_index_parameter']
            },
            'dependencies': {
                'start': ['end'],
                'end': ['start']
            }
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema())
        self.params['start'] = self.params.get('start', 0)
        self.params['end'] = self.params.get('end', 5)
        count = self.params['end'] - self.params['start']
        if count > 100:
            raise ValidationError('displayed items are over 100')
        if count < 1:
            raise ValidationError('displayed items are less than 1')

    def exec_main_proc(self):
        request_params = {
                'start': self.params['start'],
                'end': self.params['end'],
                'subject': self.event['requestContext']['authorizer']['claims']['cognito:username']
        }
        try:
            response = requests.get(
                settings.AUTHLETE_CLIENT_ENDPOINT + '/authorization/get/list',
                params=request_params,
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )

        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))

        AuthleteUtil.verify_valid_response(response)

        result = []
        for client in json.loads(response.text).get('clients', []):
            result.append({
                'clientId': client['clientId'],
                'clientName': client['clientName'],
                'clientType': client['clientType'],
                'createdAt': client['createdAt'],
                'description': client.get('description')
            })

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
