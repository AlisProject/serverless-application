import sys
import os
import shutil
import subprocess
import glob
import re
from distutils.dir_util import copy_tree

# テスト事前準備

# テスト実行のためのtmpディレクトリを作成し、testsをコピーする
os.mkdir('./tmp_tests')
copy_tree('./tests/', './tmp_tests')
execute_dir = []
exit_status = 0

# 各テストファイル毎に、テスト対象ソースと共通ライブラリをテストファイルと同一のディレクトリに複製する。
for name in glob.iglob('tmp_tests/**/test_*.py', recursive=True):
    # テストの実行ディレクトリパスを取得
    test_dir = './' + name[:name.rfind('/')]
    # テストの実行ディレクトリを追加
    execute_dir.append(test_dir)
    # テスト対象ソースを複製（対象ソースは tests 配下と同一構造の src ディレクトリ配下が対象）
    copy_tree(re.sub('^\./tmp_tests', './src', test_dir), test_dir)
    # 共通ライブラリを複製
    copy_tree('./src/common', test_dir)
    # 共通ライブラリを複製
    copy_tree('./tests/tests_common', test_dir)

for name in execute_dir:
    try:
        subprocess.check_call(['green', name])
    except subprocess.CalledProcessError:
        exit_status = 1

# tmpディレクトリは削除
shutil.rmtree('./tmp_tests')

sys.exit(exit_status)
