import asyncio
from dataclasses import dataclass
import enum
import os
from typing import List
import urllib.parse

from dataclasses_json import dataclass_json
import pyppeteer
import requests


class Scope(enum.Enum):
    INNERSCAN = 'innerscan'
    SPHYGMOMANOMETER = 'sphygmomanometer'
    PEDOMETER = 'pedometer'
    SMUG = 'smug'


@dataclass_json
@dataclass
class Token:
    access_token: str
    expires_in: int
    refresh_token: str


def auth(login_id: str, password: str, client_id: str, scope: List[Scope]) -> str:
    end_point = 'https://www.healthplanet.jp/oauth/auth'
    param = {
        'client_id': client_id,
        'redirect_uri': 'https://www.healthplanet.jp/success.html',
        'scope': ','.join(s.value for s in scope),
        'response_type': 'code',
    }
    url = '{0}?{1}'.format(end_point, urllib.parse.urlencode(param))

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_auth(url, login_id, password))
    loop.close()
    return result


async def _auth(url: str, login_id: str, password: str) -> str:
    browser = await pyppeteer.launch(headless=True)
    page = await browser.newPage()
    await page.goto(url)
    await page.type('input[name=loginId]', login_id)
    await page.type('input[name=passwd]', password)
    await asyncio.wait([
        page.click('input.mt15'),
        page.waitForNavigation(),
    ])
    await asyncio.wait([
        page.click('li.ml20 img'),
        page.waitForNavigation(),
    ])
    code = await page.querySelectorEval('textarea#code', 'e => e.value')
    await browser.close()
    return code


def token(client_id: str, client_secret: str, code: str) -> Token:
    end_point = 'https://www.healthplanet.jp/oauth/token'
    param = {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': 'https://www.healthplanet.jp/success.html',
        'code': code,
        'grant_type': 'authorization_code',
    }
    response = requests.post(end_point, data=param)
    return Token.from_json(response.text)


if __name__ == '__main__':
    code = auth(os.environ['HP_LOGIN_ID'], os.environ['HP_PASSWORD'], os.environ['HP_CLIENT_ID'], [Scope.INNERSCAN])
    token = token(os.environ['HP_CLIENT_ID'], os.environ['HP_CLIENT_SECRET'], code)
