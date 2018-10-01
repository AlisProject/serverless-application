# -*- coding: utf-8 -*-
import os
import settings
import time
import json
import logging
import traceback
from boto3.dynamodb.conditions import Key
from db_util import DBUtil
from botocore.exceptions import ClientError
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from time_util import TimeUtil


class MeArticlesLikeCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        # single
        if self.event.get('pathParameters') is None:
            raise ValidationError('pathParameters is required')
        validate(self.event.get('pathParameters'), self.get_schema())
        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.event['pathParameters']['article_id'],
            status='public'
        )

    def exec_main_proc(self):
        try:
            article_liked_user_table = self.dynamodb.Table(os.environ['ARTICLE_LIKED_USER_TABLE_NAME'])
            self.__create_article_liked_user(article_liked_user_table)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'body': json.dumps({'message': 'Already exists'})
                }
            else:
                raise

        try:
            article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
            article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
            self.__create_like_notification(article_info)
            self.__update_unread_notification_manager(article_info)
        except Exception as e:
            logging.fatal(e)
            traceback.print_exc()

        return {
            'statusCode': 200
        }

    def __create_like_notification(self, article_info):
        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
        notification_id = '-'.join([settings.LIKE_NOTIFICATION_TYPE, article_info['user_id'], article_info['article_id']])
        notification = notification_table.get_item(Key={'notification_id': notification_id}).get('Item')

        liked_count = self.__get_article_likes_count()

        if notification:
            notification_table.update_item(
                Key={
                    'notification_id': notification_id
                },
                UpdateExpression="set sort_key = :sort_key, article_title = :article_title, liked_count = :liked_count",
                ExpressionAttributeValues={
                    ':sort_key': TimeUtil.generate_sort_key(),
                    ':article_title': article_info['title'],
                    ':liked_count': liked_count
                }
            )
        else:
            Item = {
                'notification_id': notification_id,
                'user_id': article_info['user_id'],
                'article_id': article_info['article_id'],
                'article_title': article_info['title'],
                'sort_key': TimeUtil.generate_sort_key(),
                'type': settings.LIKE_NOTIFICATION_TYPE,
                'liked_count': liked_count,
                'created_at': int(time.time())
            }
            has_alias_user_id_article = True if 'alias_user_id' in article_info else False

            if has_alias_user_id_article:
                Item.update({'alias_user_id': article_info['alias_user_id']})

            notification_table.put_item(Item=Item)

    def __update_unread_notification_manager(self, article_info):
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])

        unread_notification_manager_table.update_item(
            Key={'user_id': article_info['user_id']},
            UpdateExpression='set unread = :unread',
            ExpressionAttributeValues={':unread': True}
        )

    def __create_article_liked_user(self, article_liked_user_table):
        epoch = int(time.time())
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        article_user_id = self.__get_article_user_id(self.event['pathParameters']['article_id'])
        article_liked_user = {
            'article_id': self.event['pathParameters']['article_id'],
            'user_id': user_id,
            'article_user_id': article_user_id,
            'created_at': epoch,
            'target_date': time.strftime('%Y-%m-%d', time.gmtime(epoch)),
            'sort_key': TimeUtil.generate_sort_key()
        }

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        article_user = users_table.get_item(Key={'user_id': article_user_id}).get('Item')
        user = users_table.get_item(Key={'user_id': user_id}).get('Item')
        if 'alias_user_id' in article_user:
            article_liked_user.update({'article_alias_user_id': article_user['alias_user_id']})
        if 'alias_user_id' in user:
            article_liked_user.update({'alias_user_id': user['alias_user_id']})

        article_liked_user_table.put_item(
            Item=article_liked_user,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __get_article_user_id(self, article_id):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        return article_info_table.get_item(Key={'article_id': article_id}).get('Item').get('user_id')

    def __get_article_likes_count(self):
        query_params = {
            'KeyConditionExpression': Key('article_id').eq(self.event['pathParameters']['article_id']),
            'Select': 'COUNT'
        }
        article_liked_user_table = self.dynamodb.Table(os.environ['ARTICLE_LIKED_USER_TABLE_NAME'])
        response = article_liked_user_table.query(**query_params)

        return response['Count']
