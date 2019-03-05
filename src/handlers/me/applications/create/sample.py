import json
import os

import requests


create_params = {
    'clientName': 'AAA',
    'description': 'BBB',
    'applicationType': 'WEB',
    'clientType': 'PUBLIC',
    'developer': 'matsumatsu20',
    'redirectUris': ['http://example.com']
}
try:
    response = requests.post(
        'https://api.authlete.com/api/client/create',
        json.dumps(create_params),
        headers={'Content-Type': 'application/json'},
        auth=(os.environ['AUTHLETE_API_KEY'], os.environ['AUTHLETE_API_SECRET'])
    )

    print(response.text)
except requests.exceptions.RequestException as err:
    raise Exception('Something went wrong when call Authlete API: {0}'.format(err))

