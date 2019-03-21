# -*- coding: utf-8 -*-
import boto3
from me_articles_paid_article_ids_index import MeArticlesPaidArticleIdsIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_paid_article_ids_index = MeArticlesPaidArticleIdsIndex(event=event, context=context,
                                                                                 dynamodb=dynamodb)
    return me_articles_paid_article_ids_index.main()
