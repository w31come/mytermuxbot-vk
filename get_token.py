#!/usr/bin/env python3
"""
Автоматическое получение VK токена через браузер (Playwright)
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
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0'
        )
        page = context.new_page()
        
        try:
            # 1. Открываем страницу авторизации
            log('[+] Открываем VK...')
            page.goto('https://vk.com', wait_until='networkidle', timeout=30000)
            
            # Делаем скриншот для отладки
            page.screenshot(path='debug_1_main.png')
            
            # 2. Ищем поле ввода (VK ID форма)
            log('[+] Ищем форму входа...')
            
            # Пробуем разные селекторы
            selectors = [
                'input[name="login"]',
                'input[name="email"]',
                'input[type="text"]',
                'input[placeholder*="Телефон"]',
                'input[placeholder*="Email"]',
                'input[placeholder*="Login"]',
                '.vkuiInput__el',
                'input[class*="vkuiInput"]',
                '[data-testid="login"]',
            ]
            
            login_input = None
            for sel in selectors:
                try:
                    login_input = page.locator(sel).first
                    if login_input.is_visible(timeout=2000):
                        log(f'[+] Найдено поле логина: {sel}')
                        break
                except:
                    continue
            
            if not login_input:
                log('[-] Поле логина не найдено, пробуем m.vk.com...')
                # Пробуем мобильную версию
                page.goto('https://m.vk.com', wait_until='networkidle', timeout=30000)
                page.screenshot(path='debug_2_mobile.png')
                
                # На мобильной версии
                try:
                    page.fill('input[name="email"]', login, timeout=5000)
                    page.fill('input[name="pass"]', password, timeout=5000)
                    page.click('input[type="submit"], button[type="submit"]', timeout=5000)
                except Exception as e:
                    log(f'[-] Мобильная версия тоже не сработала: {e}')
                    return None
            else:
                # Вводим логин
                login_input.fill(login)
                log('[+] Логин введён')
                
                # Ищем кнопку "Далее" или поле пароля
                time.sleep(1)
                page.screenshot(path='debug_3_after_login.png')
                
                # Пробуем нажать Enter или найти кнопку
                try:
                    page.keyboard.press('Enter')
                    log('[+] Нажали Enter')
                except:
                    try:
                        page.click('button[type="submit"]', timeout=3000)
                    except:
                        pass
                
                time.sleep(2)
                page.screenshot(path='debug_4_after_enter.png')
                
                # Ищем поле пароля
                pass_selectors = [
                    'input[name="password"]',
                    'input[type="password"]',
                    'input[placeholder*="Пароль"]',
                    'input[placeholder*="Password"]',
                    '.vkuiInput__el[type="password"]',
                ]
                
                pass_input = None
                for sel in pass_selectors:
                    try:
                        pass_input = page.locator(sel).first
                        if pass_input.is_visible(timeout=3000):
                            log(f'[+] Найдено поле пароля: {sel}')
                            break
                    except:
                        continue
                
                if pass_input:
                    pass_input.fill(password)
                    log('[+] Пароль введён')
                    
                    # Нажимаем войти
                    try:
                        page.keyboard.press('Enter')
                    except:
                        page.click('button[type="submit"]', timeout=3000)
                    
                    log('[+] Отправляем форму...')
            
            # 3. Ждём редиректа
            log('[+] Ждём авторизации...')
            time.sleep(3)
            page.screenshot(path='debug_5_after_auth.png')
            
            # Если мы на oauth.vk.com/authorize — подтверждаем доступ
            if 'authorize' in page.url:
                log('[+] Запрос доступа, подтверждаем...')
                try:
                    page.click('button[type="submit"]', timeout=10000)
                    log('[+] Доступ подтверждён')
                except:
                    log('[-] Кнопка подтверждения не найдена')
            
            # Ждём редиректа с токеном
            page.wait_for_url(lambda url: 'access_token=' in url or 'blank.html' in url, timeout=30000)
            
            # 4. Забираем токен
            url = page.url
            log(f'[+] URL: {url[:100]}...')
            
            if 'access_token=' in url:
                from urllib.parse import urlparse, parse_qs
                fragment = urlparse(url).fragment
                params = parse_qs(fragment)
                
                token = params.get('access_token', [None])[0]
                user_id = params.get('user_id', [None])[0]
                
                if token:
                    log(f'[+] Токен получен: {token[:30]}...')
                    if save_to_gist(token, scope):
                        return token
            
            # Если токена нет в URL — проверяем localStorage или cookies
            log('[-] Токен не найден в URL, пробуем другие способы...')
            
            # Пробуем получить из localStorage
            try:
                token_data = page.evaluate('''() => {
                    return localStorage.getItem('vk_access_token_settings') || 
                           localStorage.getItem('access_token') || '';
                }''')
                if token_data:
                    log(f'[+] Найден токен в localStorage')
            except:
                pass
            
            page.screenshot(path='debug_6_final.png')
            return None
            
        except Exception as e:
            log(f'[-] Ошибка: {e}')
            page.screenshot(path='error_final.png')
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
    else:
        log('[-] Не удалось получить токен.')
        exit(1)
