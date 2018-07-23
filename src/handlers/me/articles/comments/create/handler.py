# -*- coding: utf-8 -*-
import boto3
from me_articles_comments_create import MeArticlesCommentsCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_comments_create = MeArticlesCommentsCreate(event=event, context=context, dynamodb=dynamodb)
    return me_articles_comments_create.main()
