import json, requests, re, os, time, random, ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from preferences import prefs
from logger import logger

IP_LIST = {}
accounts_list = {}

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
        response = requests.get(target_url, headers=headers, proxies=proxies, timeout=20)
        return proxy, response.ok, int((time.time() - start_time) * 1000)
    except:
        return proxy, False, -1

def is_phone_number(username):
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, username) is not None

def format_phone_number(phone):
    if len(phone) == 11:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone

def format_username(username):
    if is_phone_number(username):
        return format_phone_number(username)
    return username

def load():
    myset = set()
    successful_proxies = []
    try:
        with open("src/ips.txt", "r", encoding="utf-8") as f:
            for line in f:
                ip = line.strip()
                if ":" not in ip or not ip: continue
                newIp, newPort = ip.split(':', 1)
                if not validate_ip_port(newIp, newPort): continue
                myset.add(ip)
    except Exception as e:
        pass
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(verify, proxy) for proxy in myset]
        for future in as_completed(futures):
            proxy, is_valid, requestTime = future.result()
            if is_valid:
                successful_proxies.append((proxy, requestTime))
    successful_proxies.sort(key=lambda x: x[1])
    logger.info("可用ip代理:")
    for index, (proxy, req_time) in enumerate(successful_proxies, 1):
        logger.info(f"{index}: {proxy} - {req_time}ms")
        IP_LIST[proxy] = True

def checkIn(user, pwd, ip):
    req = requests.session()
    req.headers.update(headers)
    proxies = {
        'http': f'http://{ip}',
        'https': f'http://{ip}'
    }
    req.proxies = proxies
    logger.info(f"{format_username(user)} 开始签到")
    try:
        url = 'https://bbs.binmt.cc/member.php?mod=logging&action=login&infloat=yes&handlekey=login&inajax=1&ajaxtarget=fwin_content_login'
        resp = req.get(url, proxies=proxies, timeout=20)
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
            resp = req.post(url, data=data, proxies=proxies, timeout=20)
            resp.encoding = resp.apparent_encoding
            if resp.ok:
                if '失败' in resp.text:
                    del accounts_list[user]
                    logger.warning("密码错误")
                    return
                url = 'https://bbs.binmt.cc/k_misign-sign.html'
                resp = req.get(url, proxies=proxies, timeout=20)
                resp.encoding = resp.apparent_encoding
                _formhash = formhash(resp.text)
                code = resp.status_code
                if resp.ok:
                    url = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash={_formhash}'
                    resp = req.get(url, proxies=proxies, timeout=20)
                    resp.encoding = resp.apparent_encoding
                    if '已签' in resp.text:
                        del accounts_list[user]
                        logger.info(CDATA(resp.text))
                        prefs.put(user, prefs.getTime())
                        return True
                    logger.warning(CDATA(resp.text))
    except Exception as e:
        logger.warning(f"异常: {str(e)}")
        IP_LIST[ip] = False
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
    ACCOUNTS = os.environ.get("ACCOUNTS", "")
    if not ACCOUNTS:
        logger.warning('github ACCOUNTS变量未设置')
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
            logger.info(f"{format_username(username)} 今日已签, 跳过签到")
    if accounts_list:
        load()
    if IP_LIST:
        keys = list(accounts_list.keys())
        total = len(keys)
        for i, username in enumerate(keys):
            for proxy, status in IP_LIST.items():
                if not status: continue
                try:
                    if checkIn(username, accounts_list[username], proxy): break
                except:
                    pass
            if i < total - 1:
                time.sleep(3)
start()
prefs.save()