# -*- coding: utf-8 -*-
import boto3
from labo_majority_judgement import LaboMajorityJudgement

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    target = LaboMajorityJudgement(event, context, dynamodb)
    return target.main()
