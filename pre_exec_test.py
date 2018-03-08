import glob
import re
from distutils.dir_util import copy_tree

# テスト事前準備

# 各テストファイル毎に、テスト対象ソースと共通ライブラリをテストファイルと同一のディレクトリに複製する。
for name in glob.iglob('tests/**/test*.py', recursive=True):
    # テストファイルのディレクトリパスを取得
    test_dir = re.sub('/test_.*\.py$', '', name)
    # テスト対象ソースを複製（対象ソースは tests 配下と同一構造の src ディレクトリ配下が対象）
    copy_tree(re.sub('^tests', 'src', test_dir), test_dir)
    # 共通ライブラリを複製
    copy_tree('src/common', test_dir)
