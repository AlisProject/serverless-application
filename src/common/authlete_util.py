import json
import os
import requests
import settings
from record_not_found_error import RecordNotFoundError
from jsonschema import ValidationError


class AuthleteUtil:
    @staticmethod
    def is_accessible_client(client_id, user_id):
        try:
            response = requests.get(
                settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + str(client_id),
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )

            if response.status_code == 404:
                raise RecordNotFoundError('{0} is not found.'.format(client_id))

        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))

        developer = json.loads(response.text)['developer']

        return developer == user_id

    # 400, 404以外はALIS上では異常な状態であるため、システムエラーとして扱い、検知対象にする
    @staticmethod
    def verify_valid_response(response, request_client_id=None):
        if response.status_code == 400:
            raise ValidationError('Please check the input parameters')
        if request_client_id and response.status_code == 404:
            raise RecordNotFoundError('{0} is not found.'.format(request_client_id))

        if response.status_code not in [200, 201, 204]:
            raise Exception('Something went wrong when call Authlete API: {0}, {1}'
                            .format(response.status_code, response.text))
