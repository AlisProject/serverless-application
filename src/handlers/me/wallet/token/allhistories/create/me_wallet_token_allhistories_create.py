# -*- coding: utf-8 -*-
import settings
import os
import time
import hashlib
import boto3
import io
import pytz
from decimal import Decimal, ROUND_FLOOR
from datetime import datetime
from time_util import TimeUtil
from user_util import UserUtil
from web3 import Web3, HTTPProvider
from lambda_base import LambdaBase
from record_not_found_error import RecordNotFoundError


class MeWalletTokenAllhistoriesCreate(LambdaBase):
    web3 = None
    jst = pytz.timezone('Asia/Tokyo')

    def get_schema(self):
        pass

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

        # カストディ規制時のウォレット移行が済んでいなければ利用不可
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        UserUtil.validate_private_eth_address(self.dynamodb, user_id)

    def exec_main_proc(self):
        # 必要なパラメーターを取得する
        self.web3 = Web3(HTTPProvider(os.environ['PRIVATE_CHAIN_OPERATION_URL']))
        address = self.web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS'])
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        eoa = self.__get_user_private_eth_address(user_id)

        # csvファイルを生成するためのdataの格納先の生成
        data_for_csv = io.StringIO()

        # private chainからトークンのTransferとMintのデータを取得し、csvに書き込むためのデータを準備する
        self.setTransferHistoryToData(address, eoa, data_for_csv)
        self.setMintHistoryToData(address, eoa, data_for_csv)

        # カストディ対応前にアドレスを保持していた場合は追記
        user_configuration = self.__get_user_configuration(user_id)
        if user_configuration is not None and user_configuration.get('old_private_eth_address') is not None:
            self.setTransferHistoryToData(address, user_configuration['old_private_eth_address'], data_for_csv)
            self.setMintHistoryToData(address, user_configuration['old_private_eth_address'], data_for_csv)

        # If the file is empty, then error will be raised
        if len(data_for_csv.getvalue()) == 0:
            raise RecordNotFoundError('Record Not Found')

        # 生成したデータをs3にアップロードし、生成したcsvのurlをannounce_urlとしてリターンする
        announce_url = self.extract_file_to_s3(user_id, data_for_csv)

        # ユーザーにcsvのurlを通知する
        self.__notification(user_id, announce_url)

        return {
            'statusCode': 200
        }

    def padLeft(self, eoa):
        return '0x000000000000000000000000' + eoa[2:]

    def removeLeft(self, eoa):
        return '0x' + eoa[26:]

    def add_type(self, from_eoa, to_eoa, eoa):
        alis_bridge_contract_address = os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS']
        # ssm上のBURN_ADDRESSは0xを省略しているため
        burn_address = '0x' + os.environ['BURN_ADDRESS']
        # eoa を比較用に小文字に変換
        lower_eoa = eoa.lower()

        if from_eoa == lower_eoa and to_eoa == alis_bridge_contract_address:
            return 'withdraw'
        elif from_eoa == lower_eoa and to_eoa == burn_address:
            return 'pool'
        elif from_eoa == lower_eoa and to_eoa != '0x0000000000000000000000000000000000000000':
            return 'give'
        elif from_eoa == lower_eoa and to_eoa == '0x0000000000000000000000000000000000000000':
            return 'burn'
        elif from_eoa == alis_bridge_contract_address and to_eoa == lower_eoa:
            return 'deposit'
        elif from_eoa == '---' and to_eoa == lower_eoa:
            return 'get by like'
        elif from_eoa != alis_bridge_contract_address and to_eoa == lower_eoa:
            return 'get from user'
        else:
            return 'unknown'

    def filter_transfer_data(self, transfer_result, eoa, data_for_csv):
        # 取得したデータのうち、csvファイルに書き込むデータのみを抽出し、data_for_csvに成型して書き込む
        for i in range(len(transfer_result)):
            time = datetime.fromtimestamp(
                self.web3.eth.getBlock(transfer_result[i]['blockNumber'])['timestamp']).astimezone(self.jst)
            strtime = datetime.strftime(time, "%Y/%m/%d %H:%M:%S")
            transactionHash = transfer_result[i]['transactionHash'].hex()
            type = self.add_type(self.removeLeft(transfer_result[i]['topics'][1].hex()),
                                 self.removeLeft(transfer_result[i]['topics'][2].hex()), eoa)
            amountEth = Decimal(str(self.web3.fromWei(int(transfer_result[i]['data'], 16), 'ether'))).quantize(
                Decimal("0.001"), rounding=ROUND_FLOOR)
            amountWei = int(transfer_result[i]['data'], 16)
            content_text = strtime + ',' + transactionHash + ',' + type + ',' + str(amountEth) + ',' \
                + str(amountWei) + '\n'
            data_for_csv.write(content_text)

    def setTransferHistoryToData(self, address, eoa, data_for_csv):
        # topics[0]の値がERC20のTransferイベントに一致し、topics[1](from)の値が今回データを生成するEoAにマッチするものを取得
        fromfilter = self.web3.eth.filter({
            "address": address,
            "fromBlock": 1,
            "toBlock": 'latest',
            "topics": [self.web3.sha3(text="Transfer(address,address,uint256)").hex(),
                       self.padLeft(eoa)
                       ],
        })

        # topics[0]の値がERC20のTransferイベントに一致し、topics[2](to)の値が今回データを生成するEoAにマッチするものを取得
        tofilter = self.web3.eth.filter({
            "address": address,
            "fromBlock": 1,
            "toBlock": 'latest',
            "topics": [self.web3.sha3(text="Transfer(address,address,uint256)").hex(),
                       None,
                       self.padLeft(eoa)
                       ],
        })

        # filterしたデータをすべて取得するメソッドを実行後、必要なデータだけをcsvに書き込むためのfilterを実行する
        transfer_result_from = fromfilter.get_all_entries()
        self.filter_transfer_data(transfer_result_from, eoa, data_for_csv)
        transfer_result_to = tofilter.get_all_entries()
        self.filter_transfer_data(transfer_result_to, eoa, data_for_csv)

    def filter_mint_data(self, mint_result, eoa, data_for_csv):
        # 取得したデータのうち、csvファイルに書き込むデータのみを抽出し、data_for_csvに成型して書き込む
        for i in range(len(mint_result)):
            time = datetime.fromtimestamp(
                self.web3.eth.getBlock(mint_result[i]['blockNumber'])['timestamp']).astimezone(self.jst)
            strtime = time.strftime("%Y/%m/%d %H:%M:%S")
            transactionHash = mint_result[i]['transactionHash'].hex()
            # mintデータの場合はfromを'---'に設定し、typeを判別している
            type = self.add_type('---', self.removeLeft(mint_result[i]['topics'][1].hex()), eoa)
            amountEth = Decimal(str(self.web3.fromWei(int(mint_result[i]['data'], 16), 'ether'))).quantize(
                Decimal("0.001"), rounding=ROUND_FLOOR)
            amountWei = int(mint_result[i]['data'], 16)
            content_text = strtime + ',' + transactionHash + ',' + type + ',' + str(amountEth) + ','\
                + str(amountWei) + '\n'
            data_for_csv.write(content_text)

    def setMintHistoryToData(self, address, eoa, data_for_csv):
        # topics[0]の値がMintに一致し、topics[1]の値が今回データを生成するEoAにマッチするものを取得
        to_filter = self.web3.eth.filter({
            "address": address,
            "fromBlock": 1,
            "toBlock": 'latest',
            "topics": [self.web3.sha3(text="Mint(address,uint256)").hex(),
                       self.padLeft(eoa)
                       ],
        })

        # filterしたデータをすべて取得するメソッドを実行後、必要なデータだけをcsvに書き込むためのfilterを実行する
        mint_result = to_filter.get_all_entries()
        self.filter_mint_data(mint_result, eoa, data_for_csv)

    def extract_file_to_s3(self, user_id, data_for_csv):
        bucket = os.environ['ALL_TOKEN_HISTORY_CSV_DOWNLOAD_S3_BUCKET']
        # identityIdの項目はeventの中に存在するが、IAM認証でないと取得できないためlambda側でidtokenを使い取得する実装をした
        identityId = self.__get_user_cognito_identity_id()
        key = 'private/' + identityId + '/' + user_id + '_' + datetime.now().astimezone(self.jst).strftime(
            '%Y-%m-%d-%H-%M-%S') + '.csv'
        self.upload_file(bucket, key, data_for_csv.getvalue())

        # announce_urlに生成したcsvのurlを渡す
        announce_url = 'https://' + bucket + '.s3-ap-northeast-1.amazonaws.com/' + key
        return announce_url

    def upload_file(self, bucket, key, data_for_csv):
        s3Obj = self.s3.Object(bucket, key)
        res = s3Obj.put(Body=data_for_csv)
        return res

    def __get_user_private_eth_address(self, user_id):
        # user_id に紐づく private_eth_address を取得
        user_info = UserUtil.get_cognito_user_info(self.cognito, user_id)
        private_eth_address = [a for a in user_info['UserAttributes'] if a.get('Name') == 'custom:private_eth_address']
        # private_eth_address が存在しないケースは想定していないため、取得出来ない場合は例外とする
        if len(private_eth_address) != 1:
            raise RecordNotFoundError('Record Not Found: private_eth_address')

        return private_eth_address[0]['Value']

    def __update_unread_notification_manager(self, user_id):
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])

        unread_notification_manager_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='set unread = :unread',
            ExpressionAttributeValues={':unread': True}
        )

    def __notification(self, user_id, announce_url):
        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])

        notification_id = self.__get_randomhash()

        notification_table.put_item(Item={
            'notification_id': notification_id,
            'user_id': user_id,
            'sort_key': TimeUtil.generate_sort_key(),
            'type': settings.CSVDOWNLOAD_NOTIFICATION_TYPE,
            'created_at': int(time.time()),
            'announce_body': '全トークン履歴のcsvのダウンロード準備が完了しました。本通知をクリックしてダウンロードしてください。',
            'announce_url': announce_url
        })

        self.__update_unread_notification_manager(user_id)

    def __get_randomhash(self):
        return hashlib.sha256((str(time.time()) + str(os.urandom(16))).encode('utf-8')).hexdigest()

    def __get_user_cognito_identity_id(self):
        id_token = self.event['headers']['Authorization']
        identity_pool_id = os.environ['COGNITO_IDENTITY_POOL_ID']
        region = 'ap-northeast-1'
        cognito_user_pool_id = os.environ['COGNITO_USER_POOL_ID']

        logins = {'cognito-idp.' + region + '.amazonaws.com/' + cognito_user_pool_id: id_token}
        client = boto3.client('cognito-identity', region_name=region)
        cognito_identity_id = client.get_id(
            IdentityPoolId=identity_pool_id,
            Logins=logins
        )

        return cognito_identity_id['IdentityId']

    def __get_user_configuration(self, user_id):
        user_configurations_table = self.dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        return user_configurations_table.get_item(Key={
            'user_id': user_id
        }).get('Item')
