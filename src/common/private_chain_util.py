import os
import json
import requests
import settings
import time
import re
from jsonschema import validate
from aws_requests_auth.aws_auth import AWSRequestsAuth
from exceptions import SendTransactionError, ReceiptError
from web3 import Web3, Account, HTTPProvider
from eth_account.messages import encode_defunct
from jsonschema import ValidationError
from rlp import decode
from rlp.exceptions import DecodingError


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
    def send_raw_transaction(cls, raw_transaction):
        # send_raw_transaction
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/send_raw_transaction'
        payload = {'raw_transaction': raw_transaction}
        result = PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload)

        # return transaction hash
        return json.dumps(result).replace('"', '')

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
        if result is not None:
            if result.get('logs') is not None and len(result['logs']) > 0:
                mined_logs = [log for log in result['logs'] if log.get('type') == 'mined']
                if len(mined_logs) == len(result['logs']):
                    return True
            # receipt が存在している状態で、mined ログが確認できない場合は想定外のため例外
            raise ReceiptError('Receipt exists, but Not exists mined logs.')

        return False

    @classmethod
    def get_balance(cls, private_eth_address):
        payload = {
            'private_eth_address': private_eth_address[2:]
        }
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/balance'
        return PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload)

    @classmethod
    def get_transaction_count(cls, from_user_eth_address):
        payload = {
            'from_user_eth_address': from_user_eth_address
        }
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/eth/get_transaction_count'
        return PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload)

    @classmethod
    def increment_transaction_count(cls, hex_str):
        return str(hex(int(hex_str, 16) + 1))

    @classmethod
    def get_allowance(cls, from_user_eth_address):
        payload = {
            'from_user_eth_address': from_user_eth_address,
            'owner_eth_address': from_user_eth_address[2:],
            'spender_eth_address': os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]
        }
        url = 'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/wallet/allowance'
        return PrivateChainUtil.send_transaction(request_url=url, payload_dict=payload)

    @classmethod
    def validate_message_signature(cls, message, signature, address):
        web3 = Web3(HTTPProvider(os.environ['PRIVATE_CHAIN_OPERATION_URL']))
        if web3.eth.account.recover_message(
            encode_defunct(text=message),
            signature=signature
        ) != address:
            raise ValidationError('Signature is invalid')

    @classmethod
    def validate_raw_transaction_signature(cls, transaction, address):
        if address != Account.recover_transaction(transaction):
            raise ValidationError('Signature is invalid')

    @classmethod
    def get_data_from_raw_transaction(cls, raw_transaction, transaction_count):
        try:
            # raw_transaction を decode すると下記パラメータを取得可能
            # 検証パラメータと data を除いたパラメータが正しいことを確認後 data を返却する
            # 0：nonce(transaction_count)
            # 1：gasPrice（0）
            # 2：gasLimit（0）
            # 3：to_address
            # 4：value（0）
            # 5：data
            # 6：v（検証で利用。但し、内部で chain_id が利用されているため確認対象）
            # 7：r（検証で利用）
            # 8：s（検証で利用）
            byte_data_list = decode(bytes.fromhex(raw_transaction[2:]))
            # 発生しない想定だが念の為個数を確認
            if len(byte_data_list) != 9:
                raise ValidationError('raw_transaction is invalid')
            # nonce
            if byte_data_list[0].hex() != '' and int(byte_data_list[0].hex(), 16) != int(transaction_count, 16):
                raise ValidationError('nonce is invalid')
            if byte_data_list[0].hex() == '' and int(transaction_count, 16) != 0:
                raise ValidationError('nonce is invalid')
            # gasPrice
            if byte_data_list[1].hex() != '':
                raise ValidationError('gasPrice is invalid')
            # gasLimit
            if byte_data_list[2].hex() != '0186a0':
                raise ValidationError('gasLimit is invalid')
            # to_address
            # relay method の場合は to_address は PRIVATE_CHAIN_BRIDGE_ADDRESS
            if byte_data_list[5].hex()[0:8] == 'eeec0e24':
                to_address = os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS']
            else:
                to_address = os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS']
            if byte_data_list[3].hex() != to_address[2:]:
                raise ValidationError('private_chain_alis_token_address is invalid')
            # value
            if byte_data_list[4].hex() != '':
                raise ValidationError('value is invalid')
            # v は検証パラメータだが、chain_id を含んでいるため確認する
            if byte_data_list[6].hex() not in settings.PRIVATE_CHAIN_V_VALUES:
                raise ValidationError('v is invalid')
            # data を返す
            return byte_data_list[5].hex()
        except DecodingError:
            raise ValidationError('raw_transaction is invalid')

    @classmethod
    def validate_erc20_transfer_data(cls, data, to_address):
        # length
        # method(8) + to_address(64) + tip_value(64) = 136
        if len(data) != 136:
            raise ValidationError('data is invalid')
        # method
        if data[0:8] != 'a9059cbb':
            raise ValidationError('method is invalid')
        # to_address
        if data[8:72][24:] != to_address[2:]:
            raise ValidationError('to_address is invalid')
        # tip_value
        validate(
            {'tip_value': int(data[72:], 16)},
            {
                'type': 'object',
                'properties': {
                    'tip_value': settings.parameters['tip_value']
                }
            }
        )

    @classmethod
    def validate_erc20_approve_data(cls, data):
        # length
        # method(8) + spender_eth_address(64) + value(64) = 136
        if len(data) != 136:
            raise ValidationError('data is invalid')
        # method
        if data[0:8] != '095ea7b3':
            raise ValidationError('method is invalid')
        # spender_eth_address
        if data[8:72][24:] != os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS'][2:]:
            raise ValidationError('spender_eth_address is invalid')
        # value
        if int(data[72:], 16) != 0:
            validate(
                {'token_send_value': int(data[72:], 16)},
                {
                    'type': 'object',
                    'properties': {
                        'token_send_value': settings.parameters['token_send_value']
                    }
                }
            )

    @classmethod
    def validate_erc20_relay_data(cls, data):
        # length
        # method(8) + recipient_eth_address(64) + value(64) = 136
        if len(data) != 136:
            raise ValidationError('data is invalid')
        # method
        if data[0:8] != 'eeec0e24':
            raise ValidationError('method is invalid')
        # recipient_eth_address
        if not re.fullmatch(r'0{24}[0-9a-fA-F]{40}', data[8:72]):
            raise ValidationError('recipient_eth_address is invalid')
        # value
        validate(
            {'token_send_value': int(data[72:], 16)},
            {
                'type': 'object',
                'properties': {
                    'token_send_value': settings.parameters['token_send_value']
                }
            }
        )
