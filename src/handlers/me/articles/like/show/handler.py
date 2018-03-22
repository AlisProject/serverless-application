# -*- coding: utf-8 -*-
import boto3
from me_articles_like_show import MeArticleLikeShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_like_show = MeArticleLikeShow(event=event, context=context, dynamodb=dynamodb)
    return me_articles_like_show.main()
