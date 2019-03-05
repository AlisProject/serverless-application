import json
import logging
import os

import requests

import settings


class Authorizer:
    AUTHLETE_INTROSPECTION_ENDPOINT = 'https://api.authlete.com/api/auth/introspection'

    def __init__(self, event, context):
        self.event = event
        self.context = context

    def main(self):
        http_method, resource_path = self.__extract_method_and_path(self.event['methodArn'])
        scopes = self.__get_required_scopes(http_method, resource_path)
        response = self.__introspect(scopes)

        logging.info("http_method: " + http_method)
        logging.info("resource_path: " + resource_path)
        logging.info(response)

        if response['action'] == 'OK':
            return self.__generate_policy(response['subject'], 'Allow', self.event['methodArn'])
        elif response['action'] in ['BAD_REQUEST', 'FORBIDDEN']:
            return self.__generate_policy(response['subject'], 'Deny', self.event['methodArn'])
        elif response['action'] == 'UNAUTHORIZED':
            raise Exception('Unauthorized')
        else:
            logging.info(response)
            raise Exception('Internal Server Error')

    def __introspect(self, scopes):
        try:
            response = requests.post(
                self.AUTHLETE_INTROSPECTION_ENDPOINT,
                data={'token': self.event["authorizationToken"], 'scopes': scopes},
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )
        except requests.exceptions.RequestException as e:
            logging.info(e)
            raise Exception('Internal Server Error(RequestException)')

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

    def __get_required_scopes(self, http_method, resource_path):
        # 全てのAPIcallには最低でもread権限が必要
        scopes = [settings.AUTHLETE_SCOPE_READ]

        # 未読管理の更新のみ例外としてread権限でもAPI呼び出し可能
        if resource_path == 'me/unread_notification_managers' and http_method == 'PUT':
            return scopes

        # GET以外のHTTPメソッドの場合はwriteスコープも必要
        if http_method != 'GET':
            scopes.append(settings.AUTHLETE_SCOPE_WRITE)

        return scopes

    def __extract_method_and_path(self, arn):
        arn_elements = arn.split(':', maxsplit=5)
        resource_elements = arn_elements[5].split('/', maxsplit=3)
        http_method = resource_elements[2]
        resource_path = resource_elements[3]
        return http_method, resource_path
