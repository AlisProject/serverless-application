# -*- coding: utf-8 -*-
import boto3
from me_comments_likes_create import MeCommentsLikesCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_comments_likes_create = MeCommentsLikesCreate(event=event, context=context, dynamodb=dynamodb)
    return me_comments_likes_create.main()
