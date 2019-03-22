# -*- coding: utf-8 -*-
import boto3
from me_articles_first_version_show import MeArticlesFirstVersionShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_first_version_show = MeArticlesFirstVersionShow(event=event, context=context,
                                                                dynamodb=dynamodb)
    return me_articles_first_version_show.main()
