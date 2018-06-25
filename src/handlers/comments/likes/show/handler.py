# -*- coding: utf-8 -*-
import boto3
from comments_likes_show import CommentsLikesShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    comments_likes_show = CommentsLikesShow(event=event, context=context, dynamodb=dynamodb)
    return comments_likes_show.main()
