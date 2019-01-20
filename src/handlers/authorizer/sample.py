import json

import requests

fuga = 'arn:aws:execute-api:ap-northeast-1:090169530579:5fovjh7bl3/*/GET/articles/eyecatch'

arn_elements = fuga.split(':', maxsplit=5)
resource_elements = arn_elements[5].split('/', maxsplit=3)
http_method = resource_elements[2]
resource_path = resource_elements[3]

payload = {'token': 'VSCVrvWpWN_ow5n5xgM65caf52YPbe2Vxpa2NzwVAmw'}
response = requests.post(
    "https://api.authlete.com/api/auth/introspection",
    data=payload,
    auth=('7929280486081', 'YsSgwtMX9GfLHhWAg1AZWYlsSNi5nv_4ynaDg7d0f78')
)


response_body = json.loads(response.text)

print(response_body)
