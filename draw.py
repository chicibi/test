import datetime
import time
from pprint import pprint

import requests

LITE = True


if not LITE:
    from captchagen.captchasync import poll_captcha, get_captcha_quota
    from notify.win import set_window_title
else:
    def poll_captcha(*args, **kwargs):
        pass

    def get_captcha_quota(*args, **kwargs):
        pass

    def set_window_title(*args, **kwargs):
        pass


class Context:
    token = ''  # window.DHK_ESOLUTION.ACCESS_TOKEN
    user_id = ''  # window.DHK_ESOLUTION.SSO_UID
    start_time = datetime.time(hour=10)
    start_offset = 0 # in seconds
    sleep_interval = 0.5
    proxy = None
    captcha_key = ''
    enable_captcha = True
    captcha_token = None


PROXY = {
}


def get_headers():
    headers = {
        'contentType': 'application/json;charset=UTF-8',
        'Authorization': 'Bearer ' + Context.token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0',
        'Referer': 'https://www.discoverhongkong.com/',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site'
    }
    return headers


def get_response(res):
    return dict(code=res.status_code, text=res.text)


def now():
    return datetime.datetime.now()


def wait_till_datetime(dt: datetime.datetime, sleep_interval=0.05):
    till = dt
    print(f'Wait till {till}')
    diff = None
    while True:
        current = now()
        if diff is None:
            diff = till - current
            print(f'{diff} before start')
        if current < till:
            time.sleep(sleep_interval)
        else:
            break


def wait_offset():
    dt = datetime.datetime.combine(now().date(), Context.start_time) - datetime.timedelta(seconds=Context.start_offset)
    wait_till_datetime(dt, Context.sleep_interval)


def check_login():
    url = f'https://api-es.discoverhongkong.com/customers/{Context.user_id}'
    res = requests.get(url, headers=get_headers(), proxies=Context.proxy)
    js = res.json()
    print(f'{js["mobile_phone_number_subscriber_number"]} {js["first_name"]} {js["last_name"]} {js["sso_uid"]}')


def check_wallet():
    url = f'https://api-es.discoverhongkong.com/customers/{Context.user_id}/coupons?lang=zh-Hant'
    res = requests.get(url, headers=get_headers(), proxies=Context.proxy)
    print(res.status_code)
    for x in res.json():
        if not x['is_used']:
            print(f"{x['template']['brand']['name']} - {x['template']['name']}")


def draw(camp_id, recaptcha_verify_credential=None, timeout=None):
    url = f'https://api-es.discoverhongkong.com/customers/{Context.user_id}/campaign_participation_records?lang=zh-Hant'
    data = {"campaign": str(camp_id), "desired_coupon_quantity": 1,
            "desired_coupon_publish_channel": "Discover Hong Kong Local"}

    if Context.enable_captcha:
        if recaptcha_verify_credential is None:
            recaptcha_verify_credential = Context.captcha_token
    if recaptcha_verify_credential:
        data['recaptcha_verify_credential'] = recaptcha_verify_credential
    pprint(data)
    res = requests.post(url=url, data=data, headers=get_headers(), timeout=timeout, proxies=Context.proxy)
    return get_response(res)


def d(camp_id, recaptcha_verify_credential=None, timeout=None):
    pprint(draw(camp_id))


def get_recaptcha_token():
    google_key = '6LfGbHYjAAAAAAKNROcuzJje1tz9f1yxXsDaRs1L'
    page_url = 'https://www.discoverhongkong.com/hk-tc/deals/night-treats/campaign-detail.id5332.night-treats.html?es_action_rand=Awe025'
    page_url = 'https://www.discoverhongkong.com/hk-tc/deals/in-town-offers/campaign-detail.id57.html'
    action = 'acquire_coupon'
    domain = 'recaptcha.net'
    min_score = 0.3
    enterprise = 1
    version = 'v3'
    return poll_captcha(session=requests.Session(), proxy=Context.proxy, key=Context.captcha_key, google_key=google_key,
                        page_url=page_url,
                        version=version,
                        enterprise=enterprise,
                        action=action,
                        domain=domain,
                        min_score=min_score
                        )


def get_verified_recaptcha_token(token, timeout=None):
    url = 'https://api-es.discoverhongkong.com/customers/verify-recaptcha'
    data = {
        'token': token
    }
    res = requests.post(url=url, data=data, headers=get_headers(), timeout=timeout, proxies=Context.proxy)
    js = res.json()
    print(js)
    if 'recaptcha_verify_credential' in js:
        return js['recaptcha_verify_credential']
    else:
        print(f'Error {js}')
        return None


def get_recaptcha():
    token = get_recaptcha_token()
    return get_verified_recaptcha_token(token)


def set_captcha_token(token):
    Context.captcha_token = get_verified_recaptcha_token(token)
    print(f'Verified token: {Context.captcha_token}')
    return Context.captcha_token


def check_recaptcha():
    pprint(get_captcha_quota(session=requests.Session(), proxy=Context.proxy, key=Context.captcha_key))


def loop_draw(camp_id, interval=0.5, timeout=None, max_retry=10):
    while True:
        res = draw(camp_id=camp_id, timeout=timeout)
        pprint(res)
        if res['code'] in (200, 201):
            print('------DONE------')
            break
        time.sleep(interval)
        max_retry -= 1
        print(f'Failed with retry {max_retry}')
        if max_retry < 0:
            print('Reached max retry')
            break


def loop_draw_with_wait(camp_id, interval=0.5, timeout=None):
    wait_offset()
    loop_draw(camp_id=camp_id, interval=interval, timeout=timeout)


def enable_proxy():
    Context.proxy = PROXY


def disable_proxy():
    Context.proxy = None


def t(text):
    set_window_title(text)


ld = loop_draw
lw = loop_draw_with_wait
w = check_wallet
cl = check_login
st = set_captcha_token

help = r"""
console.log('Context.token="'+window.DHK_ESOLUTION.ACCESS_TOKEN+'"\n'+'Context.user_id="'+window.DHK_ESOLUTION.SSO_UID+'"')
"""

"""
TODO:
- proxy
- wait till 12-offset
"""

print(help)
