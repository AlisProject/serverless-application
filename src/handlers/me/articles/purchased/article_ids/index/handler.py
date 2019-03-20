# -*- coding: utf-8 -*-
import boto3
from me_articles_purchased_article_ids_index import MeArticlesPurchasedArticleIdsIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_purchased_article_ids_index = MeArticlesPurchasedArticleIdsIndex(event=event, context=context,
                                                                                 dynamodb=dynamodb)
    return me_articles_purchased_article_ids_index.main()
