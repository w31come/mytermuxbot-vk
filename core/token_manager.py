import os
import json
import requests
from datetime import datetime


def log(msg):
    t = datetime.now().strftime('%H:%M:%S')
    print(f'[{t}] {msg}', flush=True)


def get_token_from_gist():
    """Забирает токен из GitHub Gist"""
    gist_id = os.environ.get('GIST_ID')
    github_token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    
    if not gist_id or not github_token:
        log('[-] Не заданы GIST_ID или GH_TOKEN')
        return None
    
    try:
        resp = requests.get(
            f'https://api.github.com/gists/{gist_id}',
            headers={
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            },
            timeout=15
        )
        resp.raise_for_status()
        
        data = resp.json()
        for filename, fileinfo in data.get('files', {}).items():
            if filename == 'vk_token.json':
                token_data = json.loads(fileinfo['content'])
                token = token_data.get('access_token')
                if token:
                    log(f'[+] Токен получен: {token[:20]}...')
                    return token
        
        log('[-] Файл vk_token.json не найден в Gist')
        return None
        
    except Exception as e:
        log(f'[-] Ошибка Gist: {e}')
        return None


def validate_token(token):
    """Проверяет валидность токена"""
    try:
        resp = requests.get(
            'https://api.vk.com/method/users.get',
            params={'access_token': token, 'v': '5.199'},
            timeout=10
        )
        data = resp.json()
        return 'error' not in data
    except:
        return False
