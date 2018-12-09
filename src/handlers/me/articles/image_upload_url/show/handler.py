# -*- coding: utf-8 -*-
import boto3
from me_articles_image_upload_url_show import MeArticlesImageUploadUrlShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_image_upload_url_show = MeArticlesImageUploadUrlShow(
        event=event, context=context, dynamodb=dynamodb
    )
    return me_articles_image_upload_url_show.main()
