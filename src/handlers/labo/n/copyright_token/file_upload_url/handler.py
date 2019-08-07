# -*- coding: utf-8 -*-
from copyright_token_file_upload_url import CopyrightTokenFileUploadUrl


def lambda_handler(event, context):
    target = CopyrightTokenFileUploadUrl(event, context)
    return target.main()
