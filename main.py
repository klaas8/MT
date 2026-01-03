import json, requests, re, os, time, random, ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from preferences import prefs

IP_LIST = set()
accounts_list = {}
successful_proxies = []

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

def validate_ip_port(ip, port):
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_multicast or ip_obj.is_unspecified:
            return False
    except ValueError:
        return False
    ip_parts = ip.split('.')
    for part in ip_parts:
        if not 0 <= int(part) <= 255:
            return False
    if not 1 <= int(port) <= 65535:
        return False
    return True

def verify(proxy):
    target_url = 'https://bbs.binmt.cc/forum.php?mod=guide&view=hot'
    proxies = {
        'https': f'http://{proxy}',
        'http': f'http://{proxy}'
    }
    start_time = time.time()
    try:
        response = requests.get(target_url, headers=headers, proxies=proxies, timeout=10)
        return proxy, response.ok, int((time.time() - start_time) * 1000)
    except:
        return proxy, False, -1

def lo():
    try:
        with open("ips.txt", "r", encoding="utf-8") as f:
            for line in f:
                ip = line.strip()
                if ":" not in ip or not ip: continue
                newIp, newPort = ip.split(':', 1)
                if not validate_ip_port(newIp, newPort): continue
                IP_LIST.add(ip)
    except Exception as e:
        pass
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(verify, proxy) for proxy in IP_LIST]
        for future in as_completed(futures):
            proxy, is_valid, requestTime = future.result()
            if is_valid:
                successful_proxies.append((proxy, requestTime))
    successful_proxies.sort(key=lambda x: x[1])

def checkIn(user, pwd, proxies):
    req = requests.session()
    req.headers.update(headers)
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
                        prefs.put(user, prefs.getTime())
                        return True
    except Exception as e:
        print(f"异常{str(e)}")
    return False

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
    keys = list(accounts_list.keys())
    total = len(keys)
    for i, username in enumerate(keys):
        for proxy, req_time in successful_proxies:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            if checkIn(username, accounts_list[username], proxies): break
        if i < total - 1:
            time.sleep(3)

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
    YiQianDao = prefs.get(username, "") == prefs.getTime()
    if username and password and not YiQianDao:
        accounts_list[username] = password
    elif YiQianDao:
        print(username, "今日已签, 跳过签到")
IP_LIST.update([ip for ip in IPS.split("\n") if ip.strip()])
if accounts_list:
    lo()
    print("ip响应时间:")
    for proxy, req_time in successful_proxies:
        print(f"{req_time}ms")
if successful_proxies:
    start()