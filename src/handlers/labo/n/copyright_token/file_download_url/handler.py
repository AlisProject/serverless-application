# -*- coding: utf-8 -*-
from copyright_token_file_download_url import CopyrightTokenFileDownloadUrl


def lambda_handler(event, context):
    target = CopyrightTokenFileDownloadUrl(event, context)
    return target.main()
