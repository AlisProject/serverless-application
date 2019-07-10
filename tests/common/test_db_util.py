import os
import time
import settings
from boto3.dynamodb.conditions import Key
from db_util import DBUtil
from jsonschema import ValidationError
from tests_util import TestsUtil
from unittest import TestCase
from record_not_found_error import RecordNotFoundError
from not_authorized_error import NotAuthorizedError


class TestDBUtil(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create article_info_table
        cls.article_info_table_items = [
            {
                'article_id': 'testid000001',
                'status': 'public',
                'user_id': 'user0001',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000002',
                'status': 'draft',
                'user_id': 'user0002',
                'sort_key': 1520150272000000,
                'price': 100,
                'version': 2
            },
            {
                'article_id': 'testid000003',
                'status': 'public',
                'user_id': 'user0002',
                'sort_key': 1520150272000000,
                'price': 1 * (10 ** 18),
                'version': 2
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], cls.article_info_table_items)

        # create article_content_table
        cls.article_content_table_items = [
            {
                'article_id': 'testid000001',
                'title': 'test_title',
                'body': 'test_body',
                'user_id': 'user0001',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000002',
                'body': 'test_body',
                'user_id': 'user0002',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000003',
                'title': 'test_title',
                'user_id': 'user0003',
                'sort_key': 1520150272000000
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_CONTENT_TABLE_NAME'], cls.article_content_table_items)

        # create users_table
        cls.users_table_items = [
            {
                'user_id': 'test01',
                'user_display_name': 'test_display_name01',
                'self_introduction': 'test_introduction01'
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['USERS_TABLE_NAME'], cls.users_table_items)

        cls.comment_items = [
            {
                'comment_id': 'comment00001',
                'article_id': 'testid000001',
                'user_id': 'commentuser01',
                'text': 'hogefugapiyo',
                'created_at': 1520150272,
                'sort_key': 1520150272000000
            },
            {
                'comment_id': 'comment00002',
                'parent_id': 'comment00001',
                'replyed_user_id': 'commentuser02',
                'article_id': 'testid000001',
                'user_id': 'test_user',
                'text': 'hogefugapiyo',
                'created_at': 1520150272,
                'sort_key': 1520150272000000
            },
            {
                'comment_id': 'comment00003',
                'article_id': 'testid000002',
                'user_id': 'commentuser03',
                'text': 'hogefugapiyo',
                'created_at': 1520150272,
                'sort_key': 1520150272000000
            },
            {
                'comment_id': 'comment00004',
                'parent_id': 'comment00003',
                'replyed_user_id': 'commentuser02',
                'article_id': 'testid000002',
                'user_id': 'commentuser04',
                'text': 'hogefugapiyo',
                'created_at': 1520150272,
                'sort_key': 1520150272000000
            }

        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['COMMENT_TABLE_NAME'], cls.comment_items)

        article_pv_user_items = [
            {
                'article_id': 'article01',
                'user_id': 'one_day_before_user1',
                'article_user_id': 'article_user_1',
                'target_date': '2018-05-01',
                'created_at': 1520035200,
                'sort_key': 1520035200000000
            },
            {
                'article_id': 'one_day_before_article',
                'user_id': 'one_day_before_user1',
                'article_user_id': 'article_user_1',
                'target_date': '2018-05-01',
                'created_at': 1520035200,
                'sort_key': 1520035200000000
            },
            {
                'article_id': 'article01',
                'user_id': 'a1_user1',
                'article_user_id': 'article_user_1',
                'target_date': '2018-05-01',
                'created_at': 1520121600,
                'sort_key': 1520121600000000
            },
            {
                'article_id': 'article01',
                'user_id': 'a1_user2',
                'article_user_id': 'article_user_1',
                'target_date': '2018-05-01',
                'created_at': 1520125200,
                'sort_key': 1520125200000000
            },
            {
                'article_id': 'article02',
                'user_id': 'a1_user2',
                'article_user_id': 'article_user_2',
                'target_date': '2018-05-02',
                'created_at': 1520125200,
                'sort_key': 1520125200000000
            }
        ]

        paid_articles_items = [
            {
                'user_id': 'purchaseuser001',
                'article_user_id': 'author001',
                'article_title': 'testtitile001',
                'price': 100 * 10 ** 18,
                'article_id': 'articleid001',
                'status': 'done',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': 1520150552000001,
                'created_at': 1520150552,
                'history_created_at': 1520150270
            },
            {
                'user_id': 'purchaseuser001',
                'article_user_id': 'author001',
                'article_title': 'testtitile001',
                'price': 100 * 10 ** 18,
                'article_id': 'articleid001',
                'status': 'fail',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': 1520150552000002,
                'created_at': 1520150552,
                'history_created_at': 1520150270
            },
            {
                'user_id': 'purchaseuser001',
                'article_user_id': 'author001',
                'article_title': 'testtitile002',
                'price': 100 * 10 ** 18,
                'article_id': 'articleid003',
                'status': 'fail',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': 1520150552000004,
                'created_at': 1520150552,
                'history_created_at': 1520150270
            },
            {
                'user_id': 'purchaseuser003',
                'article_user_id': 'author001',
                'article_title': 'testtitile002',
                'price': 100 * 10 ** 18,
                'article_id': 'articleid003',
                'status': 'doing',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': 1520150552000005,
                'created_at': 1520150553,
                'history_created_at': 1520150270
            },
            {
                'user_id': 'purchaseuser004',
                'article_user_id': 'author001',
                'article_title': 'testtitile002',
                'price': 100 * 10 ** 18,
                'article_id': 'articleid003',
                'status': 'done',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': 1520150552000006,
                'created_at': 1520150552,
                'history_created_at': 1520150270
            },
            {
                'user_id': 'purchaseuser004',
                'article_user_id': 'author001',
                'article_title': 'testtitile002',
                'price': 100 * 10 ** 18,
                'article_id': 'articleid003',
                'status': 'doing',
                'purchase_transaction': '0x0000000000000000000000000000000000000000',
                'burn_transaction': '0x0000000000000000000000000000000000000001',
                'sort_key': 1520150552000007,
                'created_at': 1520150553,
                'history_created_at': 1520150270
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['PAID_ARTICLES_TABLE_NAME'], paid_articles_items)
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_PV_USER_TABLE_NAME'], article_pv_user_items)

        topic_items = [
            {'name': 'crypto', 'order': 1, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY},
            {'name': 'fashion', 'order': 2, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY},
            {'name': 'food', 'order': 3, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY}
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['TOPIC_TABLE_NAME'], topic_items)

    def setUp(self):
        # create article_content_edit_history_table
        TestsUtil.create_table(self.dynamodb, os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'], [])

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def tearDown(self):
        # delete article_content_edit_history_table
        del_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'])
        del_table.delete()
        del_table.meta.client.get_waiter('table_not_exists').\
            wait(TableName=os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'])

    def test_exists_article_ok(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id']
        )
        self.assertTrue(result)

    def test_exists_article_ok_exists_user(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
        )
        self.assertTrue(result)

    def test_exists_article_ok_exists_status(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            status=self.article_info_table_items[0]['status']
        )
        self.assertTrue(result)

    def test_exists_article_ok_exists_user_and_status(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
            status=self.article_info_table_items[0]['status']
        )
        self.assertTrue(result)

    def test_exists_article_ng_not_exists_user_id(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id='hogefugapiyo',
        )
        self.assertFalse(result)

    def test_exists_article_ng_not_exists_article_id(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            'hogefugapiyo',
            user_id=self.article_info_table_items[0]['user_id'],
        )
        self.assertFalse(result)

    def test_exists_article_ng_not_exists_status(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
            status='draft'
        )
        self.assertFalse(result)

    def test_validate_article_existence_ok(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id']
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_status(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            status=self.article_info_table_items[0]['status']
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user_and_status(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
            status=self.article_info_table_items[0]['status']
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user_and_version1(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
            version=1
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user_and_version2(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[1]['article_id'],
            user_id=self.article_info_table_items[1]['user_id'],
            version=2
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user_and_status_and_is_purchased(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[1]['article_id'],
            user_id=self.article_info_table_items[1]['user_id'],
            status=self.article_info_table_items[1]['status'],
            is_purchased=True
        )
        self.assertTrue(result)

    def test_validate_article_existence_ng_not_exists_user_id(self):
        with self.assertRaises(NotAuthorizedError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[0]['article_id'],
                user_id='hogefugapiyo',
            )

    def test_validate_article_existence_ng_not_validate_article_existence_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                'hogefugapiyo',
                user_id=self.article_info_table_items[0]['user_id'],
            )

    def test_validate_article_existence_ng_not_exists_status(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[0]['article_id'],
                user_id=self.article_info_table_items[0]['user_id'],
                status='draft'
            )

    def test_validate_article_existence_ng_not_exists_version1(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[1]['article_id'],
                user_id=self.article_info_table_items[1]['user_id'],
                version=1
            )

    def test_validate_article_existence_ng_not_exists_version2(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[0]['article_id'],
                user_id=self.article_info_table_items[0]['user_id'],
                version=2
            )

    def test_validate_article_existence_ng_not_exists_is_purchased(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[0]['article_id'],
                user_id=self.article_info_table_items[0]['user_id'],
                is_purchased=True
            )

    def test_validate_user_existence_ok(self):
        result = DBUtil.validate_user_existence(
            self.dynamodb,
            self.users_table_items[0]['user_id']
        )
        self.assertTrue(result)

    def test_validate_user_existence_ng_not_exists_user_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_user_existence(
                self.dynamodb,
                'piyopiyo'
            )

    def test_validate_user_existence_in_thread_ok(self):
        for user_id in [self.comment_items[0]['user_id'], self.comment_items[1]['user_id']]:
            result = DBUtil.validate_user_existence_in_thread(
                self.dynamodb,
                user_id,
                self.comment_items[0]['comment_id']
            )
            self.assertTrue(result)

    def test_validate_user_existence_in_thread_with_user_id_in_other_thread(self):
        for user_id in [self.comment_items[2]['user_id'], self.comment_items[3]['user_id']]:
            with self.assertRaises(ValidationError):
                DBUtil.validate_user_existence_in_thread(
                    self.dynamodb,
                    user_id,
                    self.comment_items[0]['comment_id']
                )

    def test_validate_user_existence_in_thread_with_not_exist_id(self):
        with self.assertRaises(ValidationError):
            DBUtil.validate_user_existence_in_thread(
                self.dynamodb,
                'not_exist_id',
                self.comment_items[0]['comment_id']
            )

    def test_comment_existence_ok(self):
        result = DBUtil.comment_existence(
            self.dynamodb,
            self.comment_items[0]['comment_id']
        )
        self.assertTrue(result)

    def test_comment_existence_ng_not_exists_comment_id(self):
        result = DBUtil.comment_existence(
            self.dynamodb,
            'piyopiyo'
        )
        self.assertFalse(result)

    def test_validate_comment_existence_ok(self):
        result = DBUtil.validate_comment_existence(
            self.dynamodb,
            self.comment_items[0]['comment_id']
        )
        self.assertTrue(result)

    def test_validate_comment_existence_ng_not_exists_comment_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_comment_existence(
                self.dynamodb,
                'piyopiyo'
            )

    def test_validate_parent_comment_existence_ok(self):
        result = DBUtil.validate_parent_comment_existence(
            self.dynamodb,
            self.comment_items[0]['comment_id']
        )
        self.assertTrue(result)

    def test_validate_parent_comment_existence_ng_not_exists_comment_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_parent_comment_existence(
                self.dynamodb,
                'piyopiyo'
            )

    def test_validate_parent_comment_existence_ng_with_child_comment(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_parent_comment_existence(
                self.dynamodb,
                self.comment_items[1]['comment_id']
            )

    def test_get_validated_comment_existence_ok(self):
        result = DBUtil.get_validated_comment(
            self.dynamodb,
            self.comment_items[0]['comment_id']
        )
        self.assertEqual(result, self.comment_items[0])

    def test_get_validated_comment_ng_not_exists_comment_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.get_validated_comment(
                self.dynamodb,
                'piyopiyo'
            )

    def test_items_values_empty_to_none_ok(self):
        values = {
            'test': 'test',
            'empty': ''
        }
        DBUtil.items_values_empty_to_none(values)

        self.assertEqual(values['test'], 'test')
        self.assertEqual(values['empty'], None)

    def test_query_all_items_with_limit(self):
        article_pv_user_table = self.dynamodb.Table(os.environ['ARTICLE_PV_USER_TABLE_NAME'])
        # ユースケースとしては1MBを超え、レスポンスにLastEvaluatedKeyが付与されて返ってくる場合だが
        # Limitを付与した際も同じレスポンスなのでLimitで代用している
        query_params = {
            'IndexName': 'target_date-sort_key-index',
            'KeyConditionExpression': Key('target_date').eq('2018-05-01'),
            'Limit': 1
        }

        response = DBUtil.query_all_items(article_pv_user_table, query_params)

        self.assertEqual(len(response), 4)

    def test_query_all_items_with_no_limit(self):
        article_pv_user_table = self.dynamodb.Table(os.environ['ARTICLE_PV_USER_TABLE_NAME'])
        query_params = {
            'IndexName': 'target_date-sort_key-index',
            'KeyConditionExpression': Key('target_date').eq('2018-05-01')
        }

        response = DBUtil.query_all_items(article_pv_user_table, query_params)

        self.assertEqual(len(response), 4)

    def test_validate_topic_ok(self):
        self.assertTrue(DBUtil.validate_topic(self.dynamodb, 'crypto'))

    def test_validate_topic_ng(self):
        with self.assertRaises(ValidationError):
            DBUtil.validate_topic(self.dynamodb, 'BTC')

    def test_validate_latest_price_ok(self):
        price = 1 * (10 ** 18)
        self.assertTrue(DBUtil.validate_latest_price(self.dynamodb, 'testid000003', price))

    def test_validate_latest_price_ng(self):
        with self.assertRaises(RecordNotFoundError):
            price = 1000 * (10 ** 18)
            DBUtil.validate_latest_price(
                self.dynamodb,
                'testid000003',
                price
            )

    # 1件でもdoneかdoingが存在すればエラーを起こす
    def test_validate_not_purchased(self):
        with self.assertRaises(ValidationError):
            article_id = 'articleid001'
            user_id = 'purchaseuser001'
            DBUtil.validate_not_purchased(
                self.dynamodb,
                article_id,
                user_id
            )

    # 購入失敗のみが存在する場合は同一のuser_id, article_idの組み合わせでも購入が可能
    def test_validate_not_purchased_only_fail(self):
        article_id = 'articleid003'
        user_id = 'purchaseuser001'
        self.assertTrue(DBUtil.validate_not_purchased(
            self.dynamodb,
            article_id,
            user_id
        ))

    # 存在しない記事IDの場合にも正常終了すること
    def test_validate_not_exist_article(self):
        article_id = 'articleidxxx'
        user_id = 'purchaseuser001'
        self.assertTrue(DBUtil.validate_not_purchased(
            self.dynamodb,
            article_id,
            user_id
        ))

    # 記事のステータスがdoingの時にエラーを起こすこと
    def test_validate_status_doing(self):
        with self.assertRaises(ValidationError):
            article_id = 'articleid003'
            user_id = 'purchaseuser003'
            DBUtil.validate_not_purchased(
                self.dynamodb,
                article_id,
                user_id
            )

    # doneあるいはdoingの購入データが2件存在する場合は例外
    def test_validate_status_doing_or_done_2_cases(self):
        with self.assertRaises(ValidationError):
            article_id = 'articleid003'
            user_id = 'purchaseuser004'
            DBUtil.validate_not_purchased(
                self.dynamodb,
                article_id,
                user_id
            )

    def test_validate_exists_title_and_body_ok(self):
        result = DBUtil.validate_exists_title_and_body(
            self.dynamodb,
            'testid000001'
        )
        self.assertTrue(result)

    def test_validate_exists_title_and_body_ok_ng_not_exists_title(self):
        with self.assertRaises(ValidationError):
            DBUtil.validate_exists_title_and_body(
                self.dynamodb,
                'testid000002'
            )

    def test_validate_exists_title_and_body_ok_ng_not_exists_body(self):
        with self.assertRaises(ValidationError):
            DBUtil.validate_exists_title_and_body(
                self.dynamodb,
                'testid000003'
            )

    # article_content_edit_history の作成
    def test_put_article_content_edit_history_ok(self):
        user_id = 'test-user'
        article_id = 'test-article_id'
        body = 'test-body'
        article_content_edit_history_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'])
        settings.ARTICLE_HISTORY_PUT_INTERVAL = 0

        # 初回作成
        version = '00'
        DBUtil.put_article_content_edit_history(
            dynamodb=self.dynamodb,
            user_id=user_id,
            article_id=article_id,
            sanitized_body=body + version,
        )
        # 登録確認（version = 00 で該当データが作成されていること）
        expected_item = {
            'user_id': user_id,
            'article_edit_history_id': article_id + '_' + version,
            'body': body + version,
            'article_id': article_id,
            'version': version,
        }
        actual_items = article_content_edit_history_table.scan()['Items']
        self.assertEqual(len(actual_items), 1)
        for key in expected_item.keys():
            self.assertEqual(expected_item[key], actual_items[0][key])

        # 2回目作成
        version = '01'
        DBUtil.put_article_content_edit_history(
            dynamodb=self.dynamodb,
            user_id=user_id,
            article_id=article_id,
            sanitized_body=body + version,
        )
        # 登録確認（version = 01 で該当データが作成されていること）
        expected_item = {
            'user_id': user_id,
            'article_edit_history_id': article_id + '_' + version,
            'body': body + version,
            'article_id': article_id,
            'version': version,
        }
        actual_items = article_content_edit_history_table.scan()['Items']
        self.assertEqual(len(actual_items), 2)
        for key in expected_item.keys():
            self.assertEqual(expected_item[key], actual_items[1][key])

    # article_content_edit_history の作成（ループ有り）
    def test_put_article_content_edit_history_ok_with_loop(self):
        user_id = 'test-user'
        article_id = 'test-article_id'
        body = 'test-body'
        article_content_edit_history_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'])
        settings.ARTICLE_HISTORY_PUT_INTERVAL = 0

        # 合計で 101 回保存（ループさせる）
        for i in range(101):
            version = str(i).zfill(2)
            DBUtil.put_article_content_edit_history(
                dynamodb=self.dynamodb,
                user_id=user_id,
                article_id=article_id,
                sanitized_body=body + version,
            )

        # 意図した順序でデータを取得できること
        # article_content_edit_history を取得。body 値も確認したいため index を利用せず scan で取得し、ソートは独自に実施する。
        # (容量削減の観点で index には body を含めていないため scan で取得する必要がある)
        items = article_content_edit_history_table.scan()['Items']
        actual_items = sorted(items, key=lambda x: x['sort_key'], reverse=True)
        # 100件登録されていること
        self.assertEqual(len(actual_items), 100)
        # loop 確認。101 回実行しているため version が 00、99、98.... となる順序でデータが取得される。
        for i in range(100):
            # 先頭データはループしているため version は 00 となるが、body の内容は 101 回目に書き込んだデータが設定される
            if i == 0:
                test_version = '00'
                test_body = body + '100'
            # ループしていないデータは、99、98、.. 01 のように降順となる
            else:
                test_version = str(100 - i).zfill(2)
                test_body = body + test_version
            expected_item = {
                'user_id': user_id,
                'article_edit_history_id': article_id + '_' + test_version,
                'body': test_body,
                'article_id': article_id,
                'version': test_version,
            }
            for key in expected_item.keys():
                self.assertEqual(expected_item[key], actual_items[i][key])

    # article_content_edit_history の作成で、規定時間経過していない場合データが作成されていないこと
    def test_put_article_content_edit_history_ok_exec_before_put_interval(self):
        user_id = 'test-user'
        article_id = 'test-article_id'
        body = 'test-body'
        article_content_edit_history_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'])
        settings.ARTICLE_HISTORY_PUT_INTERVAL = 1

        # 合計で 3 回保存
        for i in range(3):
            version = str(i).zfill(2)
            DBUtil.put_article_content_edit_history(
                dynamodb=self.dynamodb,
                user_id=user_id,
                article_id=article_id,
                sanitized_body=body + version,
            )

        expected_item = {
            'user_id': user_id,
            'article_edit_history_id': article_id + '_00',
            'body': body + '00',
            'article_id': article_id,
            'version': '00'
        }

        # 最初の 1 件のみが登録されていること
        actual_items = article_content_edit_history_table.scan()['Items']
        self.assertEqual(len(actual_items), 1)
        for key in expected_item.keys():
            self.assertEqual(expected_item[key], actual_items[0][key])

    # article_content_edit_history の作成で、規定時間経過している場合、データが作成されること
    def test_put_article_content_edit_history_ok_exec_after_put_interval(self):
        user_id = 'test-user'
        article_id = 'test-article_id'
        body = 'test-body'
        article_content_edit_history_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_HISTORY_TABLE_NAME'])
        settings.ARTICLE_HISTORY_PUT_INTERVAL = 1

        # 規定時間経過後に保存
        version = '00'
        DBUtil.put_article_content_edit_history(
            dynamodb=self.dynamodb,
            user_id=user_id,
            article_id=article_id,
            sanitized_body=body + version,
        )
        # 規定時間経過
        time.sleep(settings.ARTICLE_HISTORY_PUT_INTERVAL)
        version = '01'
        DBUtil.put_article_content_edit_history(
            dynamodb=self.dynamodb,
            user_id=user_id,
            article_id=article_id,
            sanitized_body=body + version,
        )

        # 2 件登録されていること
        expected_item_1 = {
            'user_id': user_id,
            'article_edit_history_id': article_id + '_01',
            'body': body + '01',
            'article_id': article_id,
            'version': '01'
        }
        expected_item_2 = {
            'user_id': user_id,
            'article_edit_history_id': article_id + '_00',
            'body': body + '00',
            'article_id': article_id,
            'version': '00'
        }
        items = article_content_edit_history_table.scan()['Items']
        actual_items = sorted(items, key=lambda x: x['sort_key'], reverse=True)
        self.assertEqual(len(actual_items), 2)
        for key in expected_item_1.keys():
            self.assertEqual(expected_item_1[key], actual_items[0][key])
        for key in expected_item_2.keys():
            self.assertEqual(expected_item_2[key], actual_items[1][key])

    def test_get_article_content_edit_history_ok(self):
        settings.ARTICLE_HISTORY_PUT_INTERVAL = 0
        # テスト用データ作成
        target_article = self.article_info_table_items[0]
        test_body = 'test_body'
        DBUtil.put_article_content_edit_history(
            dynamodb=self.dynamodb,
            user_id=target_article['user_id'],
            article_id=target_article['article_id'],
            sanitized_body=test_body
        )
        # 該当データが取得できること
        version = '00'
        actual_item = DBUtil.get_article_content_edit_history(
            dynamodb=self.dynamodb,
            user_id=target_article['user_id'],
            article_id=target_article['article_id'],
            version=version
        )
        expected_item = {
            'user_id': target_article['user_id'],
            'article_edit_history_id': target_article['article_id'] + '_' + version,
            'body': test_body,
            'article_id': target_article['article_id'],
            'version': version,
        }
        for key in expected_item.keys():
            self.assertEqual(expected_item[key], actual_item[key])

    def test_get_article_content_edit_history_ng_not_exists_target(self):
        # 該当データが取得できない場合
        with self.assertRaises(RecordNotFoundError):
            DBUtil.get_article_content_edit_history(
                dynamodb=self.dynamodb,
                user_id='test',
                article_id='test',
                version='00'
            )
