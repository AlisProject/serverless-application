# -*- coding: utf-8 -*-
import boto3
from me_articles_images_create import MeArticlesImagesCreate

dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')


def lambda_handler(event, context):
    me_articles_images_create = MeArticlesImagesCreate(event=event, context=context, dynamodb=dynamodb, s3=s3)
    return me_articles_images_create.main()
