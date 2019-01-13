import json
import logging
import os

import requests

from lambda_base import LambdaBase


class Authorizer(LambdaBase):
    AUTHLETE_INTROSPECTION_ENDPOINT = 'https://api.authlete.com/api/auth/introspection'

    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        http_method, resource_path = self.__extract_method_and_path(self.params['methodArn'])
        scopes = self.__get_required_scopes(http_method, resource_path)
        response = self.__introspect(scopes)

        if response['action'] == 'OK':
            return self.__generate_policy(response['subject'], 'Allow', self.params['methodArn'])
        elif response['action'] in ['BAD_REQUEST', 'FORBIDDEN']:
            return self.__generate_policy(response['subject'], 'Deny', self.params['methodArn'])
        elif response['action'] == 'UNAUTHORIZED':
            raise Exception('Unauthorized')
        else:
            logging.info(response)
            raise Exception('Internal Server Error')

    def __introspect(self, scopes):
        response = requests.post(
            self.AUTHLETE_INTROSPECTION_ENDPOINT,
            data={'token': self.params["authorizationToken"], 'scopes': scopes},
            auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
        )

        return json.loads(response.text)

    def __generate_policy(self, principal_id, effect, resource):
        return {
            "principalId": principal_id,
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": 'execute-api:Invoke',
                        "Effect": effect,
                        "Resource": resource
                    }
                ]
            }
        }

    # TODO: 後追いで実装する
    def __get_required_scopes(self, http_method, resource_path):
        return []

    def __extract_method_and_path(self, arn):
        arn_elements = arn.split(':', maxsplit=5)
        resource_elements = arn_elements[5].split('/', maxsplit=3)
        http_method = resource_elements[2]
        resource_path = resource_elements[3]
        return http_method, resource_path

