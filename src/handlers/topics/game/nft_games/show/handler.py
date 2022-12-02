import os
from topics_game_nft_games_show import TopicsGameNftGamesShow
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


def lambda_handler(event, context):
    topics_game_nft_games_show = TopicsGameNftGamesShow(event, context, elasticsearch=elasticsearch)
    return topics_game_nft_games_show.main()
