import sys
import os
import shutil
import argparse
import subprocess
import glob
import re
from distutils.dir_util import copy_tree

TEST_DIR = 'tests'
TEST_TMP_DIR = './tmp_tests'


def exec_test(target_dir):
    print(target_dir)
    exit_status = 0
    try:
        subprocess.check_call(['green', '-vv', '--processes', '1', target_dir])
    except subprocess.CalledProcessError:
        exit_status = 1

    return exit_status


def copy_required_files(path):
    # テストの実行ディレクトリパスを取得
    test_dir = path[:path.rfind('/')]

    # テスト対象ソースを複製（対象ソースは tests 配下と同一構造の src ディレクトリ配下が対象）
    copy_tree(re.sub(r'^\./tmp_tests', './src', test_dir), test_dir)

    # 共通ライブラリを複製
    copy_tree('./src/common', test_dir)

    # 共通ライブラリを複製
    copy_tree('./tests/tests_common', test_dir)


def set_global_env_vers():
    os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] = 'test'
    os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'] = 'test'
    os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'] = 'test'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ignore', help='テスト対象外のディレクトリを指定。カンマ区切りで複数指定可')
    parser.add_argument('--target', help='テスト対象のディレクトリを指定')
    args = parser.parse_args()

    if os.path.isdir(TEST_TMP_DIR):
        shutil.rmtree(TEST_TMP_DIR)

    # Lambdaではファイルがフラットに展開される。tests以下を汚さないためにtmpディレクトリを準備
    os.mkdir(TEST_TMP_DIR)
    copy_tree(TEST_DIR, TEST_TMP_DIR)

    # テスト対象外のディレクトリを除却
    if args.ignore is not None:
        ignore_dirs = args.ignore.split(',')
        for ignore_dir in ignore_dirs:
            shutil.rmtree(TEST_TMP_DIR + '/' + ignore_dir)

    # テスト実行のための準備
    set_global_env_vers()
    for name in glob.iglob(TEST_TMP_DIR + '/**/test_*.py', recursive=True):
        copy_required_files(name)

    # # 引数でテストするディレクトリを受け取っている場合は変数にセットする
    target_dir = args.target if args.target is not None else ''

    result = exec_test(TEST_TMP_DIR + target_dir)

    shutil.rmtree(TEST_TMP_DIR)
    sys.exit(result)


main()
