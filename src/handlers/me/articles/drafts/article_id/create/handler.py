# -*- coding: utf-8 -*-
import boto3
from me_articles_drafts_article_id_create import MeArticlesDraftsArticleIdCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_drafts_article_id_create = MeArticlesDraftsArticleIdCreate(event, context, dynamodb)
    return me_articles_drafts_article_id_create.main()
