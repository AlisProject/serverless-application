# -*- coding: utf-8 -*-
import boto3
from majority_judgement_index import LaboNMajorityJudgementIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    target = LaboNMajorityJudgementIndex(event, context, dynamodb)
    return target.main()
