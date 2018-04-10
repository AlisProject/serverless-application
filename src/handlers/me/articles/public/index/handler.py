# -*- coding: utf-8 -*-
import boto3
from me_articles_public_index import MeArticlesPublicIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_public_index = MeArticlesPublicIndex(event, context, dynamodb)
    return me_articles_public_index.main()
