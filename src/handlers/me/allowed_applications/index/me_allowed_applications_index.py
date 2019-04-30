import os

import requests
import settings
import json
from authlete_util import AuthleteUtil
from lambda_base import LambdaBase
from jsonschema import validate


class MeAllowedApplicationsIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'start': {
                    'type': 'string'
                },
                'end': {
                    'type': 'string'
                }
            }
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        request_params = {}
        request_params['start'] = self.params.get('start', 0)
        request_params['end'] = self.params.get('end', 5)
        request_params['subject'] = [self.event['requestContext']['authorizer']['claims']['cognito:username']]

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
        for client in json.loads(response.text)['clients']:
            result.append({
                'clientId': client['clientId'],
                'clientName': client['clientName'],
                'clientType': client['clientType']
            })

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
