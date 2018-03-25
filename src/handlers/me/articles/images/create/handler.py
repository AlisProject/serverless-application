# -*- coding: utf-8 -*-
import boto3
from me_articles_images_post import MeArticlesImagesPost

dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')


def lambda_handler(event, context):
    articles_images_post = MeArticlesImagesPost(event=event, context=context, dynamodb=dynamodb, s3=s3)
    return articles_images_post.main()
