# web3.pyを用いたhandlerのテストをこのファイルで行う
import sys
import os
import shutil
import subprocess
import glob
import re
from distutils.dir_util import copy_tree
from itertools import product

TEST_DIRS = ['tests/handlers/me/articles/purchase/create']
TEST_TMP_DIR = './tmp_tests'
TARGET_TEST_TMP_DIRS = ['./tmp_tests/handlers/me/articles/purchase/create']


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
    # テスト事前準備
    if os.path.isdir(TEST_TMP_DIR):
        shutil.rmtree(TEST_TMP_DIR)

    # テスト実行のためのtmpディレクトリを作成し、testsをコピーする
    for target_test_tmp_dir, test_dir in product(TARGET_TEST_TMP_DIRS, TEST_DIRS):
        os.makedirs(target_test_tmp_dir)
        copy_tree(test_dir, target_test_tmp_dir)

    # テスト実行のための環境変数をセットする
    set_global_env_vers()

    # 引数でファイル名を受け取っている場合は変数にセットする
    target_file_path = sys.argv[1] if len(sys.argv) == 2 else None

    if target_file_path:
        # tmpフォルダ上の指定されたファイルのパスを取得
        exec_file = TEST_TMP_DIR + target_file_path[(target_file_path.find(TEST_DIR) + len(TEST_DIR)):]
        exec_dir = exec_file[:exec_file.rfind('/')]
        copy_required_files(exec_file)
    else:
        exec_dir = TEST_TMP_DIR

        for name in glob.iglob(TEST_TMP_DIR + '/**/test_*.py', recursive=True):
            copy_required_files(name)

    result = exec_test(exec_dir)

    # tmpディレクトリは削除

    shutil.rmtree(TEST_TMP_DIR)
    sys.exit(result)


main()
