# -*- coding: utf-8 -*-
import boto3
from majority_judgement_create import LaboNMajorityJudgementCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    target = LaboNMajorityJudgementCreate(event, context, dynamodb)
    return target.main()
