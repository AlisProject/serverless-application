# -*- coding: utf-8 -*-
import boto3
from me_articles_public_update_title import MeArticlesPublicUpdateTitle

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_public_update_title = MeArticlesPublicUpdateTitle(event, context, dynamodb)
    return me_articles_public_update_title.main()
