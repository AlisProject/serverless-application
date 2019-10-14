import sys
import boto3


#################################################################
# 全レコード削除対象のテーブル名を引数に実行。
# $ python delete_all_items hoge_table_name
#################################################################
def main():
    validate()
    delete_all_items(sys.argv[1])


def validate():
    if len(sys.argv) <= 1:
        print('全レコード削除対象のテーブル名を指定してください')
        exit(1)

    print(f'{sys.argv[1]} の全レコードを削除します。よろしいですか（y/n）?')
    input_str = input()
    if input_str != 'y' and input_str != 'Y':
        print('処理を中断します')
        exit(0)


def delete_all_items(table_name):
    dynamodb = boto3.resource('dynamodb')
    target_table = dynamodb.Table(table_name)
    target_items = scan_all_items(target_table)

    target_table_key_names = [k["AttributeName"] for k in target_table.key_schema]
    target_table_keys = [{k: v for k, v in i.items() if k in target_table_key_names} for i in target_items]
    with target_table.batch_writer() as batch:
        for key in target_table_keys:
            batch.delete_item(Key=key)


def scan_all_items(dynamodb_table):
    response = dynamodb_table.scan()
    items = response['Items']
    while 'LastEvaluatedKey' in response:
        response = dynamodb_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    return items


if __name__ == '__main__':
    main()
