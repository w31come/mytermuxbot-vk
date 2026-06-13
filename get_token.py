#!/usr/bin/env python3
"""
Автоматическое получение VK токена через m.vk.com (Playwright)
"""

import os
import json
import time
import requests
from playwright.sync_api import sync_playwright


def log(msg):
    print(f'[TOKEN] {msg}', flush=True)


def save_to_gist(token, scope):
    gist_id = os.environ.get('GIST_ID')
    github_token = os.environ.get('GH_TOKEN')
    
    if not gist_id or not github_token:
        log('[-] GIST_ID или GH_TOKEN не заданы')
        return False
    
    content = json.dumps({
        'access_token': token,
        'scope': scope,
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'm.vk.com'
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
    login = os.environ.get('VK_LOGIN')
    password = os.environ.get('VK_PASS')
    
    if not login or not password:
        log('[-] Не заданы VK_LOGIN и VK_PASS!')
        return None
    
    app_id = '54634841'
    scope = 'wall,friends,photos,groups,video,docs,status,offline'
    redirect = 'https://oauth.vk.com/blank.html'
    
    auth_url = (
        f'https://oauth.vk.com/authorize?'
        f'client_id={app_id}&'
        f'display=mobile&'
        f'redirect_uri={redirect}&'
        f'scope={scope}&'
        f'response_type=token&'
        f'v=5.199'
    )
    
    log('[+] Запускаем браузер...')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 375, 'height': 812},  # Мобильный вид
            user_agent='Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.0'
        )
        page = context.new_page()
        
        try:
            # 1. Сначала логинимся на m.vk.com
            log('[+] Открываем m.vk.com...')
            page.goto('https://m.vk.com', wait_until='networkidle', timeout=30000)
            page.screenshot(path='debug_1_mvk.png')
            
            # Ищем поле логина
            log('[+] Вводим логин...')
            page.fill('input[name="email"]', login, timeout=10000)
            page.fill('input[name="pass"]', password, timeout=10000)
            page.screenshot(path='debug_2_filled.png')
            
            # Нажимаем войти
            log('[+] Нажимаем "Войти"...')
            page.click('input[type="submit"], button[type="submit"]', timeout=10000)
            
            # Ждём загрузки
            page.wait_for_load_state('networkidle', timeout=30000)
            time.sleep(2)
            page.screenshot(path='debug_3_logged.png')
            
            log(f'[+] Текущий URL: {page.url}')
            
            # 2. Переходим на OAuth
            log('[+] Переходим на страницу авторизации...')
            page.goto(auth_url, wait_until='networkidle', timeout=30000)
            time.sleep(2)
            page.screenshot(path='debug_4_oauth.png')
            
            log(f'[+] URL после OAuth: {page.url}')
            
            # 3. Если запрос на доступ — подтверждаем
            if 'authorize' in page.url:
                log('[+] Подтверждаем доступ...')
                try:
                    page.click('input[type="submit"], button[type="submit"]', timeout=10000)
                    page.wait_for_load_state('networkidle', timeout=30000)
                    time.sleep(2)
                except:
                    log('[-] Кнопка подтверждения не найдена')
            else:
                log('[i] Запрос доступа не требуется')
            
            page.screenshot(path='debug_5_after_auth.png')
            
            # 4. Забираем токен из URL
            url = page.url
            log(f'[+] Финальный URL: {url[:150]}...')
            
            if 'access_token=' in url:
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
                    
                    if save_to_gist(token, scope):
                        return token
            
            # Если токена нет — пробуем из HTML
            log('[-] Токен не найден в URL, проверяем страницу...')
            html = page.content()
            if 'access_token' in html:
                log('[i] Токен найден в HTML, парсим...')
                # Простой парсинг
                import re
                match = re.search(r'access_token=([^&"\']+)', html)
                if match:
                    token = match.group(1)
                    log(f'[+] Токен из HTML: {token[:30]}...')
                    if save_to_gist(token, scope):
                        return token
            
            log('[-] Токен не найден')
            page.screenshot(path='error_final.png')
            return None
            
        except Exception as e:
            log(f'[-] Ошибка: {e}')
            page.screenshot(path='error_exception.png')
            return None
            
        finally:
            browser.close()


if __name__ == '__main__':
    log('=' * 50)
    log('VK Token Auto-Grabber (m.vk.com)')
    log('=' * 50)
    
    token = get_vk_token()
    
    if token:
        log('[+] УСПЕХ! Токен сохранён в Gist.')
    else:
        log('[-] Не удалось получить токен.')
        exit(1)
