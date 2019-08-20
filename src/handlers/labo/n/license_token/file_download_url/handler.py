# -*- coding: utf-8 -*-
from license_token_file_download_url import LicenseTokenFileDownloadUrl


def lambda_handler(event, context):
    target = LicenseTokenFileDownloadUrl(event, context)
    return target.main()
