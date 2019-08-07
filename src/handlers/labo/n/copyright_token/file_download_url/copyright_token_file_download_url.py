# -*- coding: utf-8 -*-
import os
import json
import boto3
from botocore.config import Config
from jsonschema import validate
from jsonschema import ValidationError
from lambda_base import LambdaBase
from web3 import Web3
from eth_account.messages import encode_defunct


class CopyrightTokenFileDownloadUrl(LambdaBase):
    DOWNLOAD_URL_EXPIRES = 300  # 5 Min

    COPYRIGHT_TOKEN_CONTRACT_ABI = [
        {
            "constant": True,
            "inputs": [
                {
                    "name": "tokenId",
                    "type": "uint256"
                }
            ],
            "name": "ownerOf",
            "outputs": [
                {
                    "name": "",
                    "type": "address"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]

    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'token_id': {
                    'type': 'string',
                    'pattern': r'^0x[a-fA-F0-9]{64}$'
                },
                'signature': {
                    'type': 'string',
                    'pattern': r'^0x[a-fA-F0-9]+$'
                }
            },
            'required': ['token_id', 'signature']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        s3_cli = boto3.client('s3', config=Config(signature_version='s3v4'), region_name='ap-northeast-1')
        bucket = os.environ['LABO_S3_BUCKET_NAME']

        # トークンを保持しているかチェック
        self.__check_token_owner(self.params['token_id'], self.params['signature'])

        # トークンIDに対応するファイルのキーを取得
        key = self.__get_object_key_for_token_id(s3_cli, bucket, self.params['token_id'])

        # ダウンロードURLを生成
        download_url = s3_cli.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=self.DOWNLOAD_URL_EXPIRES,
            HttpMethod='GET'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'download_url': download_url
            })
        }

    def __get_object_key_for_token_id(self, s3_cli, bucket, token_id):
        prefix = 'copyright_token/' + token_id + '/'
        list_objects_response = s3_cli.list_objects(Bucket=bucket, Prefix=prefix)

        # オブジェクトが存在しない場合はエラー
        if 'Contents' not in list_objects_response \
                or len(list_objects_response['Contents']) <= 0:
            raise ValidationError('Invalid token_id - File not found')

        return list_objects_response['Contents'][0]['Key']

    def __check_token_owner(self, token_id, signature):
        # web3の初期化
        provider = Web3.HTTPProvider(os.environ['PUBLIC_CHAIN_OPERATION_URL'])
        web3 = Web3(provider)

        # 署名からEOAのアドレスを復元
        try:
            data = f"この署名は下記IDの著作権トークンを保有していることの証明に利用されます。\n{token_id}"
            sender_address = web3.eth.account.recover_message(encode_defunct(text=data), signature=signature)
        except Exception:
            raise ValidationError('Invalid signature')

        # トークンの所有者を取得
        copyright_token_contract = web3.eth.contract(
            web3.toChecksumAddress(os.environ['PUBLIC_CHAIN_COPYRIGHT_TOKEN_ADDRESS']),
            abi=self.COPYRIGHT_TOKEN_CONTRACT_ABI)
        try:
            owner_address = copyright_token_contract.functions.ownerOf(int(token_id, 16)).call()
        except Exception:
            # トークンが存在しないためエラー
            raise ValidationError('Invalid token_id - Token not found')

        # トークンの保有者では無い場合はエラー
        if owner_address != sender_address:
            raise ValidationError('Not owner of the token')
