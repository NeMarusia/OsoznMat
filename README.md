# OsoznMat

Telegram-бот для сценария «Осознанное материнство».

Стек: Python 3, aiogram 3, YAML-сценарий, SQLite, Docker Compose. Бот работает через polling. Медиа отправляются из локальных папок `images/` и `videos/`; публичная статика и nginx не используются.

## Структура

- `bot/` — код бота и движок сценария.
- `data/flow.yaml` — граф сообщений, кнопки, переходы, таймеры и ссылки.
- `data/text_issues.md` — замечания по текстам без автоматических исправлений.
- `images/` — изображения для отправки.
- `images/data.txt` — описание привязки изображений к сообщениям.
- `videos/` — видеофайлы для отправки.
- `videos/data.txt` — описание привязки видео к сообщениям.
- `storage/` — SQLite-хранилище состояния пользователей.
- `tests/` — автотесты YAML, структуры данных, медиа и проверки ответа `КК-20`.

## Настройка

```bash
cp .env.example .env
```

В `.env` нужно указать:

```env
BOT_TOKEN=123456:replace_me
FLOW_PATH=data/flow.yaml
DATABASE_PATH=storage/bot.sqlite3
IMAGES_DIR=images
VIDEOS_DIR=videos
LOG_LEVEL=INFO
```

## Запуск локально

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m bot.main
```

## Запуск через Docker Compose

```bash
docker compose up -d --build
```

Логи:

```bash
docker compose logs -f bot
```

Остановка:

```bash
docker compose down
```

## Проверка

```bash
pytest
```

Тесты проверяют:

- синтаксис `data/flow.yaml`;
- структуру узлов графа;
- существование всех переходов;
- сохранность UTM-параметров в ссылках;
- наличие описанных медиафайлов;
- варианты правильного и неправильного ответа в `КК-20`.

## Как менять сценарий

Основная логика лежит в `data/flow.yaml`. У каждого узла есть `id`, текст, кнопки, переходы и, если нужно, медиа.

Пример кнопки-перехода:

```yaml
buttons:
  - text: Интересно
    target: kk31
```

Пример кнопки-ссылки:

```yaml
buttons:
  - text: Записаться
    url: https://example.com/?utm_source=bot
```

Пример медиа:

```yaml
media:
  - type: video
    path: videos/dykhalka.mp4
```

Если в узле несколько изображений, бот отправит их как Telegram media group.

## Важное

Тексты перенесены без редакторских исправлений. Все подозрительные места вынесены в `data/text_issues.md`.

