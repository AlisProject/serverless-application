# -*- coding: utf-8 -*-
from license_token_file_upload_url import LicenseTokenFileUploadUrl


def lambda_handler(event, context):
    target = LicenseTokenFileUploadUrl(event, context)
    return target.main()
