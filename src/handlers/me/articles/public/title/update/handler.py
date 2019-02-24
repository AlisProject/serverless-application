# -*- coding: utf-8 -*-
import boto3
from me_articles_public_title_update import MeArticlesPublicTitleUpdate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_public_title_update = MeArticlesPublicTitleUpdate(event, context, dynamodb)
    return me_articles_public_title_update.main()
