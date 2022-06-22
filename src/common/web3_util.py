import os
import json
import re
import requests
import asyncio
from exceptions import Web3ServiceApiError
from web3 import Web3


class Web3Util:
    BADGE_CONTRACT_ABI = [
        {
            "constant": True,
            "inputs": [
                {
                    "internalType": "address",
                    "name": "owner",
                    "type": "address"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [
                {
                    "internalType": "address",
                    "name": "owner",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "index",
                    "type": "uint256"
                }
            ],
            "name": "tokenOfOwnerByIndex",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "tokenId",
                    "type": "uint256"
                }
            ],
            "name": "tokenURI",
            "outputs": [
                {
                    "internalType": "string",
                    "name": "",
                    "type": "string"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "name": "badgeTypeSupply",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]

    @staticmethod
    def create_contract_object(operation_url, abi, contract_address):
        # web3の初期化
        provider = Web3.HTTPProvider(operation_url)
        web3 = Web3(provider)
        # コントラクトの作成
        return web3.eth.contract(web3.toChecksumAddress(contract_address), abi=abi)

    @staticmethod
    def create_badge_contract_object():
        response = requests.get(os.environ['WEB3_SERVICE_BASE_URL'] + '/api/badge/eth_address')
        if response.status_code is not 200:
            raise Web3ServiceApiError(response.text)
        badge_address = json.loads(response.text)['badge_contract_address']
        return Web3Util.create_contract_object(os.environ['BADGE_OPERATION_URL'], Web3Util.BADGE_CONTRACT_ABI,
                                               badge_address)

    @staticmethod
    def get_badge_types(user_id):
        badge_contract = Web3Util.create_badge_contract_object()
        response = requests.get(f"{os.environ['WEB3_SERVICE_BASE_URL']}/api/users/{user_id}/eth_address")
        if response.status_code is not 200:
            raise Web3ServiceApiError(response.text)
        # バッジ連携していない場合は空配列を返却
        badge_address = json.loads(response.text).get('public_chain_address')
        result = []
        if badge_address is None:
            return result
        # 該当ユーザの全バッジのtypeを取得
        # バッジの数を取得
        badge_len = badge_contract.functions.balanceOf(badge_address).call()
        # バッジの情報を並列に取得
        loop = asyncio.get_event_loop()
        coros = [Web3Util.__get_badge_type(badge_contract, badge_address, i, loop) for i in range(badge_len)]
        groups = asyncio.gather(*coros)
        results = loop.run_until_complete(groups)
        return list(set(results))

    @staticmethod
    async def __get_badge_type(badge_contract, badge_address, badge_index, loop):
        # トークンIDを取得
        token_id = await loop.run_in_executor(None, badge_contract.functions.tokenOfOwnerByIndex(badge_address,
                                                                                                 badge_index).call)
        # トークンのメタデータURIを取得
        token_uri = await loop.run_in_executor(None, badge_contract.functions.tokenURI(token_id).call)
        type_match = re.match('.*/(\\d+)/metadata.json', token_uri)
        if type_match is not None:
            return int(type_match.group(1))
        return 0
