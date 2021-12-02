import boto3
from me_articles_drafts_delete import MeArticlesDraftsDelete

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_drafts_delete = MeArticlesDraftsDelete(event, context, dynamodb=dynamodb)
    return me_articles_drafts_delete.main()
