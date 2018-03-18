# -*- coding: utf-8 -*-
import boto3
from articles_likes_post import ArticlesLikesPost

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_article_id_likes_post = ArticlesLikesPost(event=event, context=context, dynamodb=dynamodb)
    return articles_article_id_likes_post.main()
