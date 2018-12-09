import json
import os
import uuid

import boto3
from jsonschema import validate

import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from parameter_util import ParameterUtil
from user_util import UserUtil


class MeArticlesImageUploadUrlShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'upload_image_size': settings.parameters['upload_image_size'],
                'upload_image_extension': settings.parameters['upload_image_extension']
            },
            'required': ['article_id', 'upload_image_size', 'upload_image_extension']
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        UserUtil.verified_phone_and_email(self.event)
        validate(self.params, self.get_schema())
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.event['pathParameters']['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username']
        )

    def exec_main_proc(self):
        s3_cli = boto3.client('s3')
        bucket = os.environ['DIST_S3_BUCKET_NAME']

        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        file_name = str(uuid.uuid4()) + '.' + self.params['upload_image_extension']
        key = settings.S3_ARTICLES_IMAGES_PATH + user_id + '/' + self.params['article_id'] + '/' + file_name

        content_length = self.params['upload_image_size']

        post = s3_cli.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            ExpiresIn=300,
            Conditions=[
                ["content-length-range", content_length, content_length]
            ]
        )

        return {
            'statusCode': 200,
            'body': json.dumps(post)
        }
