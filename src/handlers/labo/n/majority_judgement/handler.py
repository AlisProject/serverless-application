# -*- coding: utf-8 -*-
import boto3
from majority_judgement import LaboNMajorityJudgement

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    target = LaboNMajorityJudgement(event, context, dynamodb)
    return target.main()
