import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
import json
from typing import List
import urllib.parse

from dataclasses_json import config, dataclass_json, Undefined
import pyppeteer
import requests


class Scope(Enum):
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


class InnerscanTag(Enum):
    WEIGHT = '6021'
    BODY_FAT = '6022'
    MUSCLE_MASS = '6023'
    MUSCLE_SCORE = '6024'
    VISCERAL_FAT_2 = '6025'
    VISCERAL_FAT_1 = '6026'
    BASAL_METABOLIC_RATE = '6027'
    BODY_AGE = '6028'
    BONE_MASS = '6029'


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class InnerscanRecord:
    tag: InnerscanTag
    measured: datetime = field(metadata=config(field_name='date', decoder=lambda x: datetime.strptime(x, '%Y%m%d%H%M%S')))
    keydata: Decimal = field(metadata=config(decoder=lambda x: Decimal(x)))


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


def innerscan(access_token: str, from_datetime: datetime, to_datetime: datetime, tag: List[InnerscanTag]) -> List[InnerscanRecord]:
    end_point = 'https://www.healthplanet.jp/status/innerscan.json'
    param = {
        'access_token': access_token,
        'date': 1,
        'from': from_datetime.strftime('%Y%m%d%H%M%S'),
        'to': to_datetime.strftime('%Y%m%d%H%M%S'),
        'tag': ','.join(t.value for t in tag),
    }
    response = requests.post(end_point, data=param)
    result = json.loads(response.text)['data']
    return [InnerscanRecord.from_dict(r) for r in result]
