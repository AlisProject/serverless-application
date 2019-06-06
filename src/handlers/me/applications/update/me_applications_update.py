import json
import os

import requests
from jsonschema import validate, FormatChecker

import settings
from authlete_util import AuthleteUtil
from lambda_base import LambdaBase
from no_permission_error import NoPermissionError
from parameter_util import ParameterUtil


class MeApplicationUpdate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'name': settings.parameters['oauth_client']['name'],
                'description': settings.parameters['oauth_client']['description'],
                'client_id': settings.parameters['oauth_client']['client_id'],
                'redirect_urls': settings.parameters['oauth_client']['redirect_urls']
            },
            'required': ['client_id', 'name', 'redirect_urls']
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema(), format_checker=FormatChecker())

        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        if not AuthleteUtil.is_accessible_client(self.params['client_id'], user_id):
            raise NoPermissionError('No permission on this resource')

    def exec_main_proc(self):
        # update 前のアプリケーション情報を取得
        now_application_info = self.get_application_info()
        # update 前のアプリケーション情報を元にアプリケーション情報を更新
        result = self.update_application_info(now_application_info)

        return {
            'statusCode': 200,
            'body': result.text
        }

    def update_application_info(self, application_info):
        application_info['clientName'] = self.params['name']
        application_info['description'] = self.params.get('description')
        application_info['redirectUris'] = self.params['redirect_urls']

        try:
            response = requests.post(
                settings.AUTHLETE_CLIENT_ENDPOINT + '/update/' + str(self.params['client_id']),
                json.dumps(application_info),
                headers={'Content-Type': 'application/json'},
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )
        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))
        AuthleteUtil.verify_valid_response(response, request_client_id=self.params['client_id'])
        return response

    def get_application_info(self):
        try:
            response = requests.get(
                settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + str(self.params['client_id']),
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )
        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))
        AuthleteUtil.verify_valid_response(response, request_client_id=self.params['client_id'])
        return json.loads(response.text)
