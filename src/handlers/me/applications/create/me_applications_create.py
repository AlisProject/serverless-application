import json
import os
import requests
from jsonschema import validate, FormatChecker

import settings
from authlete_util import AuthleteUtil
from lambda_base import LambdaBase
from user_util import UserUtil


class MeApplicationsCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'name': settings.parameters['oauth_client']['name'],
                'description': settings.parameters['oauth_client']['description'],
                'application_type': settings.parameters['oauth_client']['application_type'],
                'redirect_urls': settings.parameters['oauth_client']['redirect_urls']
            },
            'required': ['name', 'application_type', 'redirect_urls']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        validate(self.params, self.get_schema(), format_checker=FormatChecker())

    def exec_main_proc(self):
        create_params = {
            'clientName': self.params['name'],
            'description': self.params.get('description'),
            'applicationType': self.params['application_type'],
            'tokenAuthMethod': self.__get_token_auth_method(self.params['application_type']),
            'clientType': self.__get_client_type_from_application_type(self.params['application_type']),
            'developer': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            'redirectUris': self.params['redirect_urls'],
            'grantTypes': ['AUTHORIZATION_CODE', 'REFRESH_TOKEN'],
            'responseTypes': ['CODE']
        }
        try:
            response = requests.post(
                settings.AUTHLETE_CLIENT_ENDPOINT + '/create',
                json.dumps(create_params),
                headers={'Content-Type': 'application/json'},
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )
        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))

        AuthleteUtil.verify_valid_response(response)

        return {
            'statusCode': 200,
            'body': response.text
        }

    def __get_client_type_from_application_type(self, application_type):
        if application_type == 'WEB':
            return 'CONFIDENTIAL'
        elif application_type == 'NATIVE':
            return 'PUBLIC'
        else:
            raise ValueError('Invalid application_type')

    def __get_token_auth_method(self, application_type):
        if application_type == 'WEB':
            return 'CLIENT_SECRET_BASIC'
        elif application_type == 'NATIVE':
            return 'NONE'
        else:
            raise ValueError('Invalid application_type')
