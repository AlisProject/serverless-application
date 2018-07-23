import sys
import os
import shutil
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
    copy_tree(re.sub('^\./tmp_tests', './src', test_dir), test_dir)

    # 共通ライブラリを複製
    copy_tree('./src/common', test_dir)

    # 共通ライブラリを複製
    copy_tree('./tests/tests_common', test_dir)


def main():
    # テスト事前準備
    if os.path.isdir(TEST_TMP_DIR):
        shutil.rmtree(TEST_TMP_DIR)

    # テスト実行のためのtmpディレクトリを作成し、testsをコピーする
    os.mkdir(TEST_TMP_DIR)
    copy_tree(TEST_DIR, TEST_TMP_DIR)

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
