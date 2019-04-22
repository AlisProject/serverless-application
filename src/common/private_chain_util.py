import os
import json
import requests
import settings
import time
from aws_requests_auth.aws_auth import AWSRequestsAuth
from exceptions import SendTransactionError


class PrivateChainUtil:
    auth = None

    @classmethod
    def __set_aws_requests_auth(cls):
        if cls.auth is None:
            cls.auth = AWSRequestsAuth(
                aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                aws_region='ap-northeast-1',
                aws_service='execute-api'
            )

    @classmethod
    def send_transaction(cls, request_url, payload_dict=None):
        cls.__set_aws_requests_auth()
        headers = {"content-type": "application/json"}

        # send transaction
        if payload_dict is None:
            response = requests.post(request_url, auth=cls.auth, headers=headers)
        else:
            response = requests.post(request_url, auth=cls.auth, headers=headers, data=json.dumps(payload_dict))

        # validate status code
        if response.status_code != 200:
            raise SendTransactionError('status code not 200')

        # validate exists error
        if json.loads(response.text).get('error'):
            raise SendTransactionError(json.loads(response.text).get('error'))

        # return result
        return json.loads(response.text).get('result')

    @classmethod
    def is_transaction_completed(cls, transaction):
        count = 0
        is_completed = False
        while count < settings.TRANSACTION_CONFIRM_COUNT:
            count += 1
            # get receipt of target transaction
            payload = {'transaction_hash': transaction}
            request_url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/transaction/receipt'
            result = cls.send_transaction(request_url=request_url, payload_dict=payload)
            # 完了しているかを確認
            if PrivateChainUtil.__is_completed_receipt_result(result):
                is_completed = True
                break
            # 完了が確認できなかった場合は 1 秒待機後に再実施
            time.sleep(1)
        return is_completed

    @classmethod
    def __is_completed_receipt_result(cls, result):
        # 全ての log が完了となっていることを確認
        if result is not None and result.get('logs') is not None and len(result['logs']) > 0:
            mined_logs = [log for log in result['logs'] if log.get('type') == 'mined']
            if len(mined_logs) == len(result['logs']):
                return True
        return False
