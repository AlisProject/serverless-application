# -*- coding: utf-8 -*-
import boto3
from me_articles_content_edit_histories_index import MeArticlesContentEditHistoriesIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_content_edit_histories_index = MeArticlesContentEditHistoriesIndex(event, context, dynamodb)
    return me_articles_content_edit_histories_index.main()
