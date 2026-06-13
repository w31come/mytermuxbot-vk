# VK Auto Poster 🤖

Репозиторий: `w31come/mytermuxbot-vk`  
Mini App ID: `54634841`

## Как работает

1. **Mini App** (VK) → обновляет токен в GitHub Gist
2. **GitHub Actions** → забирает токен из Gist → постит в группы

## Настройка

### 1. Mini App
- Открой: https://vk.com/app54634841
- Введи GitHub Token
- Нажми "Получить и сохранить"
- Скопируй **Gist ID**

### 2. Секреты репозитория
Settings → Secrets and variables → Actions → New repository secret

| Secret | Значение |
|--------|----------|
| `GIST_ID` | ID Gist из Mini App |
| `GH_TOKEN` | GitHub Token (ghp_...) |

### 3. Запуск
Actions → VK Auto Poster → Run workflow

Или жди автозапуска каждый час.

## Структура

| Файл | Назначение |
|------|-----------|
| `config/groups.py` | Список групп для постинга |
| `config/settings.py` | Настройки (App ID, задержки) |
| `core/token_manager.py` | Обновление токена из Gist |
| `core/vk_api.py` | VK API wrapper |
| `core/text_generator.py` | Генерация текста постов |
| `main.py` | Основной цикл постинга |
