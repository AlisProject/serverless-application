# -*- coding: utf-8 -*-
import boto3
from pre_signup import PreSignUp

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    presignup = PreSignUp(event=event, context=context, dynamodb=dynamodb, cognito=cognito)
    return presignup.main()
