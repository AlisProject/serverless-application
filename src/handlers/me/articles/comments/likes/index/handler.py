# -*- coding: utf-8 -*-
import boto3
from me_articles_comments_likes_index import MeArticlesCommentsLikesIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_comments_likes_index = MeArticlesCommentsLikesIndex(event=event, context=context, dynamodb=dynamodb)
    return me_articles_comments_likes_index.main()
