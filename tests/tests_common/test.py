from tests_util import TestsUtil
from decimal import Decimal
import os

dynamodb = TestsUtil.get_dynamodb_client()
TestsUtil.set_all_tables_name_to_env()
TestsUtil.delete_all_tables(dynamodb)

paid_article_items = [
    {
        'user_id': 'purchaseuser001',
        'article_user_id': 'author001',
        'article_title': 'purchase001 titile',
        'price': 100 * (10 ** 18),
        'article_id': 'publicId0004',
        'status': 'fail',
        'purchase_transaction': '0x0000000000000000000000000000000000000000',
        'sort_key': Decimal(1520150552000003),
        'created_at': Decimal(int(1520150552.000003)),
        'history_created_at': Decimal(1520150270)
    }
]
TestsUtil.create_table(dynamodb, os.environ['PAID_ARTICLES_TABLE_NAME'], paid_article_items)

paid_status_items = [
    {
        'user_id': 'purchaseuser001',
        'article_id': 'publicId0004',
        'status': 'doing'
    }
]

paid_status_table = dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
res = paid_status_table.get_item(Key={
    'article_id': "publicId0004",
    'user_id': 'purchaseuser001'
}).get('Item')
print(res)
