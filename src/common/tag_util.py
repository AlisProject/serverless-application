import os
import time


class TagUtil:
    @classmethod
    def create_and_count(cls, dynamodb, before_tag_names, after_tag_names):
        tag_table = dynamodb.Table(os.environ['TAG_TABLE_NAME'])

        if before_tag_names is None:
            before_tag_names = []

        if after_tag_names is None:
            after_tag_names = []

        for tag_name in after_tag_names:
            if before_tag_names is None or tag_name not in before_tag_names:
                if tag_table.get_item(Key={'name': tag_name}).get('Item'):
                    # タグが追加された場合カウントを+1する
                    TagUtil.update_count(tag_table, tag_name, 1)
                # タグがDBに存在しない場合は新規作成する
                else:
                    tag_table.put_item(
                        Item={
                            'name': tag_name,
                            'count': 1,
                            'created_at': int(time.time())
                        }
                    )

        # タグが外された場合カウントを-1する
        for tag_name in before_tag_names:
            if tag_name not in after_tag_names:
                if tag_table.get_item(Key={'name': tag_name}).get('Item'):
                    cls.update_count(tag_table, tag_name, -1)

    @classmethod
    def update_count(cls, table, tag_name, num):
        table.update_item(
            Key={'name': tag_name},
            UpdateExpression='set #attr = #attr + :increment',
            ExpressionAttributeNames={'#attr': 'count'},
            ExpressionAttributeValues={':increment': num}
        )
