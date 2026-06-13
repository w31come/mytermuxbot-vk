#!/usr/bin/env python3
import time
import sys
from datetime import datetime

from config.groups import GROUP_IDS
from config.settings import DELAY_BETWEEN_POSTS, CYCLE_PAUSE
from core.token_manager import get_token_from_gist, validate_token
from core.vk_api import VKAPI
from core.text_generator import generate


def log(msg):
    t = datetime.now().strftime('%H:%M:%S')
    print(f'[{t}] {msg}', flush=True)


def main():
    log('=' * 50)
    log('VK Auto Poster v1.0 | App ID: 54634841')
    log('=' * 50)
    
    token = get_token_from_gist()
    if not token:
        log('[-] Не удалось получить токен из Gist')
        sys.exit(1)
    
    if not validate_token(token):
        log('[-] Токен невалиден')
        sys.exit(1)
    
    vk = VKAPI(token)
    
    me = vk.get_me()
    if 'error' in me:
        log(f'[-] Ошибка авторизации: {me["error"]}')
        sys.exit(1)
    
    user = me['response'][0]
    log(f'[+] Авторизован: {user["first_name"]} {user["last_name"]}')
    log(f'[+] Групп для постинга: {len(GROUP_IDS)}')
    
    cycle = 0
    while True:
        cycle += 1
        log(f"\n{'='*40}")
        log(f'🔄 Цикл #{cycle}  {datetime.now():%H:%M:%S}')
        log(f'{'='*40}')
        
        posted = 0
        skipped = 0
        errors = 0
        
        for i, gid in enumerate(GROUP_IDS, 1):
            log(f'[{i}/{len(GROUP_IDS)}] Группа {gid}...')
            
            msg = generate()
            result = vk.post_to_wall(gid, msg)
            
            if 'error' in result:
                code = result['error'].get('error_code')
                
                if code == 5:
                    log('[-] Токен протух! Останавливаемся.')
                    sys.exit(1)
                elif code == 15:
                    log(f'[-] Нет прав для поста в {gid}')
                    skipped += 1
                elif code == 214:
                    log(f'[-] Стена {gid} закрыта')
                    skipped += 1
                elif code == 9:
                    log(f'[-] Flood control в {gid}')
                    errors += 1
                else:
                    log(f'[-] Ошибка {code}: {result["error"]}')
                    errors += 1
            else:
                pid = result['response']['post_id']
                log(f'✅ Пост: https://vk.com/wall-{gid}_{pid}')
                posted += 1
            
            if i < len(GROUP_IDS):
                log(f'⏳ Пауза {DELAY_BETWEEN_POSTS}с...')
                time.sleep(DELAY_BETWEEN_POSTS)
        
        log(f'{'='*40}')
        log(f'✅ Цикл #{cycle}: {posted} постов, {skipped} пропущено, {errors} ошибок')
        log(f'{'='*40}')
        
        log(f'⏸️ ПЕРЕРЫВ {CYCLE_PAUSE // 60} МИНУТ')
        for left in range(CYCLE_PAUSE, 0, -60):
            minutes = left // 60
            log(f'⏳ До следующего цикла: {minutes} мин...')
            time.sleep(60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log('\n⚠️ ОСТАНОВЛЕНО')
        sys.exit(0)
