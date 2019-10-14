# -*- coding: utf-8 -*-
import boto3
from majority_judgement_delete_all import LaboNMajorityJudgementDeleteAll

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    target = LaboNMajorityJudgementDeleteAll(event, context, dynamodb)
    return target.main()
