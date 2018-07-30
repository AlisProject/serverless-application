# -*- coding: utf-8 -*-
import boto3
from topics_index import TopicsIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    topics_index = TopicsIndex(event=event, context=context, dynamodb=dynamodb)
    return topics_index.main()
