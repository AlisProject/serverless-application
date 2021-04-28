from crypto_ranking_index import CryptoRankingIndex


def lambda_handler(event, context):
    crypto_ranking_index = CryptoRankingIndex(event=event, context=context)
    return crypto_ranking_index.main()
