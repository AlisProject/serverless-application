# -*- coding: utf-8 -*-
import boto3
from pre_signup import PreSignUp

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    presignup = PreSignUp(event=event, context=context, dynamodb=dynamodb)
    return presignup.main()
