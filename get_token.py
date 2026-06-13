#!/usr/bin/env python3
"""
Автоматическое получение VK токена через браузер (Playwright)
Запускать ТОЛЬКО вручную через GitHub Actions
"""

import os
import json
import time
import requests
from playwright.sync_api import sync_playwright


def log(msg):
    print(f'[TOKEN] {msg}', flush=True)


def save_to_gist(token, scope):
    """Сохраняет токен в Gist"""
    gist_id = os.environ.get('GIST_ID')
    github_token = os.environ.get('GH_TOKEN')
    
    if not gist_id or not github_token:
        log('[-] GIST_ID или GH_TOKEN не заданы')
        return False
    
    content = json.dumps({
        'access_token': token,
        'scope': scope,
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'playwright_auto'
    }, indent=2)
    
    try:
        resp = requests.patch(
            f'https://api.github.com/gists/{gist_id}',
            headers={
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            },
            json={
                'files': {
                    'vk_token.json': {
                        'content': content
                    }
                }
            },
            timeout=15
        )
        resp.raise_for_status()
        log('[+] Токен сохранён в Gist!')
        return True
    except Exception as e:
        log(f'[-] Ошибка сохранения: {e}')
        return False


def get_vk_token():
    """Автоматический вход в VK и получение токена"""
    login = os.environ.get('VK_LOGIN')
    password = os.environ.get('VK_PASS')
    
    if not login or not password:
        log('[-] Не заданы VK_LOGIN и VK_PASS в секретах!')
        return None
    
    # Параметры OAuth
    app_id = '54634841'  # Твой Mini App ID (или любой другой)
    scope = 'wall,friends,photos,groups,video,docs,status,offline'
    redirect = 'https://oauth.vk.com/blank.html'
    
    auth_url = (
        f'https://oauth.vk.com/authorize?'
        f'client_id={app_id}&'
        f'display=page&'
        f'redirect_uri={redirect}&'
        f'scope={scope}&'
        f'response_type=token&'
        f'v=5.199'
    )
    
    log('[+] Запускаем браузер...')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.0'
        )
        page = context.new_page()
        
        try:
            # 1. Открываем страницу авторизации
            log('[+] Открываем VK...')
            page.goto(auth_url, wait_until='networkidle', timeout=30000)
            
            # 2. Вводим логин/пароль
            log('[+] Вводим данные...')
            page.fill('input[name="email"], input[name="login"]', login, timeout=10000)
            page.fill('input[name="pass"], input[name="password"]', password, timeout=10000)
            
            # 3. Нажимаем войти
            page.click('button[type="submit"], .VkIdForm__signInButton', timeout=10000)
            
            # 4. Ждём редиректа на blank.html с токеном
            log('[+] Ждём авторизации...')
            page.wait_for_url(lambda url: 'access_token=' in url or 'blank.html' in url, timeout=30000)
            
            # 5. Если запрос на доступ — подтверждаем
            if 'authorize' in page.url:
                log('[+] Подтверждаем доступ...')
                page.click('button[type="submit"], .grant_access', timeout=10000)
                page.wait_for_url(lambda url: 'access_token=' in url, timeout=30000)
            
            # 6. Забираем токен из URL
            url = page.url
            log(f'[+] URL: {url[:100]}...')
            
            if 'access_token=' in url:
                # Парсим токен
                from urllib.parse import urlparse, parse_qs
                fragment = urlparse(url).fragment
                params = parse_qs(fragment)
                
                token = params.get('access_token', [None])[0]
                user_id = params.get('user_id', [None])[0]
                expires = params.get('expires_in', ['0'])[0]
                
                if token:
                    log(f'[+] Токен получен: {token[:30]}...')
                    log(f'[+] User ID: {user_id}')
                    log(f'[+] Expires: {expires}')
                    
                    # Сохраняем в Gist
                    if save_to_gist(token, scope):
                        return token
            
            log('[-] Токен не найден в URL')
            # Скриншот для отладки
            page.screenshot(path='error.png')
            return None
            
        except Exception as e:
            log(f'[-] Ошибка: {e}')
            page.screenshot(path='error.png')
            return None
            
        finally:
            browser.close()


if __name__ == '__main__':
    log('=' * 50)
    log('VK Token Auto-Grabber (Playwright)')
    log('=' * 50)
    
    token = get_vk_token()
    
    if token:
        log('[+] УСПЕХ! Токен сохранён в Gist.')
        log('[+] Теперь запусти основной workflow.')
    else:
        log('[-] Не удалось получить токен.')
        log('[i] Проверь логин/пароль в секретах.')
        exit(1)
