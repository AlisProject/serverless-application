from topics_crypto_ranking_index import TopicsCryptoRankingIndex


def lambda_handler(event, context):
    topics_crypto_ranking_index = TopicsCryptoRankingIndex(event=event, context=context)
    return topics_crypto_ranking_index.main()
