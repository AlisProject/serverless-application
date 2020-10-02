# -*- coding: utf-8 -*-
import boto3
from users_articles_popular import UsersArticlesPopular

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    users_articles_popular = UsersArticlesPopular(event, context, dynamodb)
    return users_articles_popular.main()
