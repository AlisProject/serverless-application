import os
import boto3
from topics_game_nft_games_ranking_index import TopicsGameNftGamesRankingIndex
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


awsauth = AWS4Auth(
    os.environ['AWS_ACCESS_KEY_ID'],
    os.environ['AWS_SECRET_ACCESS_KEY'],
    os.environ['AWS_REGION'],
    'es',
    session_token=os.environ['AWS_SESSION_TOKEN']
)
elasticsearch = Elasticsearch(
    hosts=[{'host': os.environ['ELASTIC_SEARCH_ENDPOINT'], 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    topics_game_nft_games_ranking_index = TopicsGameNftGamesRankingIndex(event, context, dynamodb=dynamodb,
                                                                         elasticsearch=elasticsearch)
    return topics_game_nft_games_ranking_index.main()
