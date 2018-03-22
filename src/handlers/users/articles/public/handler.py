# -*- coding: utf-8 -*-
import boto3
from users_articles_public import UsersArticlesPublic

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    users_articles_public = UsersArticlesPublic(event, context, dynamodb)
    return users_articles_public.main()
