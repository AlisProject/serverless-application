# -*- coding: utf-8 -*-
import os
import settings
import uuid
import base64
import json
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from PIL import Image
from io import BytesIO


class MeArticlesImagesCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'article_image': settings.parameters['article_image']
            },
            'required': ['article_id', 'article_image']
        }

    def get_headers_schema(self):
        return {
            'type': 'object',
            'properties': {
                'Content-Type': {
                    'type': 'string',
                    'enum': [
                        'image/gif',
                        'image/jpeg',
                        'image/png'
                    ]
                }
            },
            'required': ['Content-Type']
        }

    def validate_image_data(self, image_data):
        try:
            Image.open(BytesIO(base64.b64decode(image_data)))
        except Exception as e:
            raise ValidationError('Bad Request: No supported image format')

    def validate_params(self):
        # single
        # params
        validate(self.params, self.get_schema())
        self.validate_image_data(self.params['article_image'])
        # headers
        validate(self.event.get('headers'), self.get_headers_schema())

        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.event['pathParameters']['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username']
        )

    def exec_main_proc(self):
        ext = self.headers['Content-Type'].split('/')[1]
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        key = user_id + '/' + self.params['article_id'] + '/' + str(uuid.uuid4()) + '.' + ext
        image_data = self.__get_save_image_data(base64.b64decode(self.params['article_image']), ext)

        self.s3.Bucket(os.environ['ARTICLES_IMAGES_BUCKET_NAME']).put_object(
            Body=image_data,
            Key=key,
            ContentType=self.headers['Content-Type']
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'image_url': key})
        }

    def __get_save_image_data(self, image_data, ext):
        image = Image.open(BytesIO(image_data))
        w, h = image.size
        if w <= settings.ARTICLE_IMAGE_MAX_WIDTH and h <= settings.ARTICLE_IMAGE_MAX_HEIGHT:
            return image_data

        image.thumbnail((settings.ARTICLE_IMAGE_MAX_WIDTH, settings.ARTICLE_IMAGE_MAX_HEIGHT), Image.ANTIALIAS)
        buf = BytesIO()
        image.save(buf, format=ext)
        return buf.getvalue()
