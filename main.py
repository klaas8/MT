import json
import requests
import re
import os
import time
import random
from preferences import prefs

WX_PUSHER_APP_TOKEN = os.environ.get("WX_PUSHER_APP_TOKEN", "")
WX_PUSHER_UID = os.environ.get("WX_PUSHER_UID", "")

s = set()
ip = ""
total_retry_count = 0
MAX_RETRY = 3
Retry = {}
accounts_list = {}
s_list = {}
prefs.put("theme", "dark")
"""
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

def verify():
    global ip
    target_url = 'https://bbs.binmt.cc/forum.php?mod=guide&view=hot'
    max_attempts = min(len(s), 100)
    attempt_count = 0
    while s and attempt_count < max_attempts:
        attempt_count += 1
        if not s:
            break
        proxy = random.choice(list(s))
        print(f"{attempt_count}: {proxy}")
        proxies = {
            'https': f'http://{proxy}',
            'http': f'http://{proxy}'
        }
        try:
            response = requests.get(target_url, headers=headers, proxies=proxies, timeout=10)
            if response.status_code == 200:
                print("✔")
                ip = proxy
                s.remove(proxy)
                return
        except Exception as e:
            pass
        s.remove(proxy)
        print("✖")
        time.sleep(0.1)

def checkIn(user, pwd):
    req = requests.session()
    req.headers.update(headers)
    proxies = {
        'http': f'http://{ip}',
        'https': f'http://{ip}'
    }
    req.proxies = proxies
    print(user, "开始签到")
    try:
        url = 'https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login'
        resp = req.get(url, proxies=proxies, timeout=10)
        resp.encoding = resp.apparent_encoding
        if resp.ok:
            content = resp.text
            _loginhash = loginhash(content)
            _formhash = formhash(content)
            url = f'https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=login&loginhash={_loginhash}&inajax=1'
            data = {
                'formhash': _formhash,
                'referer': 'https://bbs.binmt.cc/k_misign-sign.html',
                'fastloginfield': 'username',
                'username': user,
                'password': pwd,
                'questionid': '0',
                'answer': '',
                'agreebbrule': ''
            }
            resp = req.post(url, data=data, proxies=proxies, timeout=10)
            resp.encoding = resp.apparent_encoding
            if resp.ok:
                if '失败' in resp.text:
                    del accounts_list[user]
                    print("密码错误")
                    return
                url = 'https://bbs.binmt.cc/k_misign-sign.html'
                resp = req.get(url, proxies=proxies, timeout=10)
                resp.encoding = resp.apparent_encoding
                _formhash = formhash(resp.text)
                code = resp.status_code
                if resp.ok:
                    url = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={_formhash}'
                    resp = req.get(url, proxies=proxies, timeout=10)
                    resp.encoding = resp.apparent_encoding
                    print(CDATA(resp.text))
                    if '已签' in resp.text:
                        del accounts_list[user]
                        s_list[user] = "签到成功";
    except Exception as e:
        print(f"异常{str(e)}")
        Retry[user] = pwd
        s_list[user] = "签到失败";

def wx_pusher_send_by_webapi(title, msg):
    if not WX_PUSHER_APP_TOKEN or not WX_PUSHER_UID: return False;
    webapi = 'http://wxpusher.zjiecode.com/api/send/message'
    data = {
        "appToken": WX_PUSHER_APP_TOKEN,
        "content": msg,
        "summary": title,
        "contentType": 1,
        "uids": [WX_PUSHER_UID],
    }
    result = requests.post(url=webapi, json=data)
    if result.ok:
        return result.json()["code"] == 1000;

def loginhash(data):
    pattern = r'loginhash.*?=(.*?)[\'"]>'
    match = re.search(pattern, data, re.IGNORECASE | re.UNICODE)
    if match and match.group(1):
        return match.group(1).strip()
    return ''

def formhash(data):
    pattern = r'formhash[\'"].*?value=[\'"](.*?)[\'"].*?/>'
    match = re.search(pattern, data, re.IGNORECASE | re.UNICODE)
    if match and match.group(1):
        return match.group(1).strip()
    return ''

def CDATA(data):
    pattern = r'CDATA.*?(.*?)]>'
    match = re.search(pattern, data, re.IGNORECASE | re.UNICODE)
    if match and match.group(1):
        return match.group(1).strip('[]')
    return ''

def start():
    global Retry, total_retry_count
    if Retry and total_retry_count < MAX_RETRY:
        total_retry_count += 1
        for key, value in Retry.items():
            accounts_list[key] = value
        Retry.clear()
    if accounts_list:
        verify()
        if not ip: return
        keys = list(accounts_list.keys())
        total = len(keys)
        for i, username in enumerate(keys):
            checkIn(username, accounts_list[username])
            if i < total - 1:
                time.sleep(3)
        start()
        return;
    wx_pusher_send_by_webapi("MT论坛签到通知", json.dumps(s_list, indent=4, ensure_ascii=False));

ACCOUNTS = os.environ.get("ACCOUNTS", "")
IPS = os.environ.get("IPS", "")
if not IPS:
    print('github IPS变量未设置')
    exit(1)
if not ACCOUNTS:
    print('github ACCOUNTS变量未设置')
    exit(1)
for duo in ACCOUNTS.split(","):
    if ':' not in duo:
        continue
    username, password = duo.split(':', 1)
    username = username.strip()
    password = password.strip()
    if username and password:
        accounts_list[username] = password
s.update([ip for ip in IPS.split("\n") if ip.strip()])
start()
"""