# -*- coding: utf-8 -*-
import boto3
from me_articles_like_create import MeArticlesLikeCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_article_id_likes_post = MeArticlesLikeCreate(event=event, context=context, dynamodb=dynamodb)
    return articles_article_id_likes_post.main()
