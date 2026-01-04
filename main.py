import json, requests, re, os, time, random, ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from preferences import prefs

key = f"{prefs.getTimes()}_{random.uniform(0, 100)}"
print(key)
prefs.put("cs", key)
myset = set()
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
        response = requests.get(target_url, headers=headers, proxies=proxies, timeout=10)
        return proxy, response.ok, int((time.time() - start_time) * 1000)
    except:
        return proxy, False, -1

def lo():
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
    successful_proxies = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(verify, proxy) for proxy in myset]
        for future in as_completed(futures):
            proxy, is_valid, requestTime = future.result()
            if is_valid:
                successful_proxies.append((proxy, requestTime))
                if len(successful_proxies) >= 10: break
    successful_proxies.sort(key=lambda x: x[1])
    print("ip响应时间:")
    for index, (proxy, req_time) in enumerate(successful_proxies, 1):
        print(f"{index}: {req_time}ms")
        myset.add(proxy)

def checkIn(user, pwd, ip):
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
        for proxy in myset:
            try:
                if checkIn(username, accounts_list[username], proxy): break
            except Exception as e:
                pass
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
myset.update([ip for ip in IPS.split("\n") if ip.strip()])
if accounts_list or not accounts_list:
    lo()
    try:
        with open("y.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(myset))
        try:
            os.system('git config --local user.name "github-actions[bot]" >/dev/null 2>&1')
            os.system('git config --local user.email "github-actions[bot]@users.noreply.github.com" >/dev/null 2>&1')
            os.system('git config pull.rebase true >/dev/null 2>&1')
            os.system(f'git add -A >/dev/null 2>&1')
            os.system('git commit -m "更新" >/dev/null 2>&1')
            os.system('git push --quiet --force-with-lease')
        except Exception as e:
            pass
    except Exception as e:
        pass
if myset:
    start()