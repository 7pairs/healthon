import os
import urllib.parse
import webbrowser


def auth(client_id: str, redirect_uri: str, scope: str, response_type: str) -> None:
    end_point = 'https://www.healthplanet.jp/oauth/auth'
    param = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'response_type': response_type,
    }
    url = '{0}?{1}'.format(end_point, urllib.parse.urlencode(param))
    webbrowser.open(url)


if __name__ == '__main__':
    auth(os.environ['HP_CLIENT_ID'], 'https://www.healthplanet.jp/success.html', 'innerscan', 'code')
