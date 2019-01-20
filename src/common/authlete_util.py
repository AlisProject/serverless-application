import json
import os
import requests
import settings
from record_not_found_error import RecordNotFoundError


class AuthleteUtil:
    @staticmethod
    def is_accessible_client(client_id, user_id):
        try:
            response = requests.get(
                settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + client_id,
                auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
            )
        except requests.exceptions.RequestException as err:
            raise Exception('Something went wrong when call Authlete API: {0}'.format(err))

        developer = json.loads(response.text)['developer']

        return developer == user_id

    # 404以外はALIS上では異常な状態であるため、システムエラーとして扱い、検知対象にする
    @staticmethod
    def verify_valid_response(response, request_client_id=None):
        if request_client_id and response.status_code == 404:
            raise RecordNotFoundError('{0} is not found.'.format(request_client_id))

        if response.status_code != 200:
            raise Exception('Something went wrong when call Authlete API: {0}, {1}'
                            .format(response.status_code, response.text))
