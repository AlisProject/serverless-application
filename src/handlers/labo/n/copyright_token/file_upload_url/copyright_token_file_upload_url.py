# -*- coding: utf-8 -*-
import os
import json
import boto3
from botocore.config import Config
from jsonschema import validate
from jsonschema import ValidationError
from lambda_base import LambdaBase
from parameter_util import ParameterUtil


class CopyrightTokenFileUploadUrl(LambdaBase):
    UPLOAD_URL_EXPIRES = 300  # 5 Min
    UPLOAD_FILE_SIZE_MAXIMUM = 52428800  # 50 MB

    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'token_id': {
                    'type': 'string',
                    'pattern': r'^0x[a-fA-F0-9]{64}$'
                },
                'upload_file_size': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': self.UPLOAD_FILE_SIZE_MAXIMUM
                },
                'upload_file_name': {
                    'type': 'string'
                }
            },
            'required': ['token_id', 'upload_file_size', 'upload_file_name']
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        s3_cli = boto3.client('s3', config=Config(signature_version='s3v4'), region_name='ap-northeast-1')

        bucket = os.environ['LABO_S3_BUCKET_NAME']
        prefix = 'copyright_token/' + self.params['token_id'] + '/'
        key = prefix + self.params['upload_file_name']
        content_length = self.params['upload_file_size']

        # トークンIDに紐づくフォルダが既に存在する場合に、ファイルの作成・上書きを禁止する
        list_objects_response = s3_cli.list_objects(Bucket=bucket, Prefix=prefix)
        if 'Contents' in list_objects_response \
                and len(list_objects_response['Contents']) > 0:
            raise ValidationError('Token id is duplicated.')

        upload_url = s3_cli.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': bucket, 'Key': key,
                    'ContentLength': content_length},
            ExpiresIn=self.UPLOAD_URL_EXPIRES,
            HttpMethod='PUT'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'upload_url': upload_url
            })
        }
