# -*- coding: utf-8 -*-
import os
import settings
import uuid
import base64
import json
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from PIL import Image
from io import BytesIO


class MeInfoIconCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'icon_image': settings.parameters['icon_image']
            },
            'required': ['icon_image']
        }

    def get_headers_schema(self):
        return {
            'type': 'object',
            'properties': {
                'content-type': {
                    'type': 'string',
                    'enum': [
                        'image/gif',
                        'image/jpeg',
                        'image/png'
                    ]
                }
            },
            'required': ['content-type']
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
        self.validate_image_data(self.params['icon_image'])
        # headers
        validate(self.event.get('headers'), self.get_headers_schema())

    def exec_main_proc(self):
        ext = self.headers['content-type'].split('/')[1]
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        key = user_id + '/icon/' + str(uuid.uuid4()) + '.' + ext
        image_data = self.__get_save_image_data(base64.b64decode(self.params['icon_image']), ext)

        self.s3.Bucket(os.environ['ME_INFO_ICON_BUCKET_NAME']).put_object(
            Body=image_data,
            Key=key,
            ContentType=self.headers['content-type']
        )

        self.__update_user_info(key)

        return {
            'statusCode': 200,
            'body': json.dumps({'icon_image_url': key})
        }

    def __update_user_info(self, icon_image_url):
        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])

        users_table.update_item(
            Key={
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            },
            UpdateExpression='set icon_image_url=:icon_image_url',
            ExpressionAttributeValues={
                ':icon_image_url': icon_image_url,
            }
        )

    def __get_save_image_data(self, image_data, ext):
        image = Image.open(BytesIO(image_data))
        w, h = image.size
        if w <= settings.USER_ICON_WIDTH and h <= settings.USER_ICON_HEIGHT:
            return image_data

        # resize to icon size
        if w >= h and (h > settings.USER_ICON_HEIGHT):
            resize_rate = h / settings.USER_ICON_HEIGHT
            image.thumbnail((w / resize_rate, settings.USER_ICON_HEIGHT), Image.ANTIALIAS)
        elif (h > w) and (w > settings.USER_ICON_WIDTH):
            resize_rate = w / settings.USER_ICON_WIDTH
            image.thumbnail((settings.USER_ICON_WIDTH, h / resize_rate), Image.ANTIALIAS)

        # crop image to square
        w, h = image.size
        crop_width = settings.USER_ICON_WIDTH if w >= settings.USER_ICON_WIDTH else w
        crop_height = settings.USER_ICON_HEIGHT if h >= settings.USER_ICON_HEIGHT else h
        crop_image = self.__crop_center(image, crop_width, crop_height)
        buf = BytesIO()
        crop_image.save(buf, format=ext)
        return buf.getvalue()

    def __crop_center(self, image_data, crop_width, crop_height):
        w, h = image_data.size
        return image_data.crop((
            (w - crop_width) // 2,
            (h - crop_height) // 2,
            (w + crop_width) // 2,
            (h + crop_height) // 2
        ))
