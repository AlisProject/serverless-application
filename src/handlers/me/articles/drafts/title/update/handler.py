# -*- coding: utf-8 -*-
import boto3
from me_articles_drafts_title_update import MeArticlesDraftsTitleUpdate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_drafts_title_update = MeArticlesDraftsTitleUpdate(event, context, dynamodb)
    return me_articles_drafts_title_update.main()
