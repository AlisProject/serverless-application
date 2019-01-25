# -*- coding: utf-8 -*-
import boto3
from me_articles_drafts_update_body import MeArticlesDraftsUpdateBody

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_drafts_update_body = MeArticlesDraftsUpdateBody(event, context, dynamodb)
    return me_articles_drafts_update_body.main()
