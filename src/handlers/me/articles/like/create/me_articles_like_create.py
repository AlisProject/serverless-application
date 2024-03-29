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
from user_util import UserUtil
from twitter_util import TwitterUtil


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
        UserUtil.verified_phone_and_email(self.event)
        if self.event['requestContext']['authorizer']['claims'].get('custom:private_eth_address') is None:
            raise ValidationError('not exists private_eth_address')

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
        # 「いいね」情報登録処理
        article_info = self.__get_article_info(self.event['pathParameters']['article_id'])
        article_user_id = article_info.get('user_id')
        try:
            article_liked_user_table = self.dynamodb.Table(os.environ['ARTICLE_LIKED_USER_TABLE_NAME'])
            self.__create_article_liked_user(article_liked_user_table, article_user_id)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'body': json.dumps({'message': 'Already exists'})
                }
            else:
                raise

        # 通知情報登録処理。「セルフいいね」だった場合は通知を行わない
        liked_count = self.__get_article_likes_count()
        if article_user_id != self.event['requestContext']['authorizer']['claims']['cognito:username']:
            try:
                article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
                article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
                self.__create_like_notification(article_info, liked_count)
                self.__update_unread_notification_manager(article_info)
            except Exception as e:
                logging.fatal(e)
                traceback.print_exc()

        # 一定回数いいねされた場合 tweet を行う
        if liked_count == settings.LIKED_TWEET_COUNT:
            self.__post_tweet(user_id=article_user_id, title=article_info.get('title'), tags=article_info.get('tags'))

        return {
            'statusCode': 200
        }

    def __create_like_notification(self, article_info, liked_count):
        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])
        notification_id = '-'.join([settings.LIKE_NOTIFICATION_TYPE, article_info['user_id'], article_info['article_id']])
        notification = notification_table.get_item(Key={'notification_id': notification_id}).get('Item')

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
            notification_table.put_item(Item={
                    'notification_id': notification_id,
                    'user_id': article_info['user_id'],
                    'article_id': article_info['article_id'],
                    'article_title': article_info['title'],
                    'sort_key': TimeUtil.generate_sort_key(),
                    'type': settings.LIKE_NOTIFICATION_TYPE,
                    'liked_count': liked_count,
                    'created_at': int(time.time())
                }
            )

    def __update_unread_notification_manager(self, article_info):
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])

        unread_notification_manager_table.update_item(
            Key={'user_id': article_info['user_id']},
            UpdateExpression='set unread = :unread',
            ExpressionAttributeValues={':unread': True}
        )

    def __create_article_liked_user(self, article_liked_user_table, article_user_id):
        epoch = int(time.time())
        article_liked_user = {
            'article_id': self.event['pathParameters']['article_id'],
            'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            'article_user_id': article_user_id,
            'created_at': epoch,
            'target_date': time.strftime('%Y-%m-%d', time.gmtime(epoch)),
            'sort_key': TimeUtil.generate_sort_key()
        }
        article_liked_user_table.put_item(
            Item=article_liked_user,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __get_article_info(self, article_id):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        return article_info_table.get_item(Key={'article_id': article_id}).get('Item')

    def __get_article_likes_count(self):
        query_params = {
            'KeyConditionExpression': Key('article_id').eq(self.event['pathParameters']['article_id']),
            'Select': 'COUNT'
        }
        article_liked_user_table = self.dynamodb.Table(os.environ['ARTICLE_LIKED_USER_TABLE_NAME'])
        response = article_liked_user_table.query(**query_params)

        return response['Count']

    def __post_tweet(self, user_id, title, tags):
        # tweet 文の作成
        # title 文(50文字以上は省略)
        if len(title) > 50:
            show_title = title[:50] + '...'
        else:
            show_title = title
        # hash tag 文(最大55文字)
        hash_tags_str = ''
        if tags:
            for tag in tags:
                if hash_tags_str == '':
                    hash_tags_str += '\n#' + tag
                elif len(hash_tags_str + tag) < 55:
                    hash_tags_str += ' #' + tag
                else:
                    break
        # tweet 文
        payload = {
            "text": f"{show_title}\n"
                    f"https://{os.environ['DOMAIN']}/{user_id}/articles/{self.event['pathParameters']['article_id']}" +
                    hash_tags_str + "\n※人気記事ボット🤖"
        }
        # tweet 実施
        twitter_util = TwitterUtil(
            consumer_key=os.environ['TWITTER_APP_CONSUMER_KEY'],
            consumer_secret=os.environ['TWITTER_APP_CONSUMER_SECRET'],
            access_token=os.environ['TWITTER_APP_ACCESS_TOKEN'],
            access_token_secret=os.environ['TWITTER_APP_ACCESS_TOKEN_SECRET']
        )
        twitter_util.post_tweet(payload)
