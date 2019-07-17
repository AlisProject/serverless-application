import os
import shutil
import argparse
import subprocess
import glob

# AWS Lambda へのデプロイ用ファイル（zip）を handler.py ファイル毎に作成する
# 前提
# pip install が完了していること（./venv/lib/python3.6/site-packages/ 配下に必要ライブラリが作成済であること）


# 事前処理

# デプロイディレクトリを空にする
DEPLOY_PATH = os.getcwd() + '/deploy/'
if os.path.exists(DEPLOY_PATH):
    shutil.rmtree(DEPLOY_PATH)
os.makedirs(DEPLOY_PATH)

# 引数を取得
parser = argparse.ArgumentParser()
parser.add_argument('--target', help='パッケージングする関数のhandlerへのパスを指定')
args = parser.parse_args()


# deploy 用 zip ファイルを作成
def make_deploy_zip(zip_file_name, target_dir):
    # zip 作成（実行ファイルパス）
    exec_zip(zip_file_name, target_dir)
    # zip 追加（共通ライブラリ）
    exec_zip(zip_file_name, 'src/common')
    # zip 追加（venv ライブラリ）
    exec_zip(zip_file_name, 'vendor-package')


# zip ファイル作成実行
def exec_zip(zip_file_name, zip_target_dir):
    cmd = 'cd ' + os.getcwd() + '/' + zip_target_dir + '; zip -r ' + DEPLOY_PATH + zip_file_name + ' ./*'
    subprocess.check_call(cmd, shell=True)


# --- メイン処理 ---


# 引数でパッケージングする関数のhandlerへのパスを受け取っている場合は変数にセットする
# デフォルトはすべてのリソースをパッケージング
target = args.target if args.target is not None else 'src/handlers/**/handler.py'

# 各 handler ファイル毎に、共通ライブラリと venv のライブラリを含めて zip ファイルを作成する
for name in glob.iglob(target, recursive=True):
    # 実行ディレクトリパスを取得
    target = './' + name[:name.rfind('/')]
    # zip のファイル名を取得
    zip_file_name = target[len('./src/handlers/'):].replace('/', '_') + '.zip'
    # zip 作成
    make_deploy_zip(zip_file_name, target)
