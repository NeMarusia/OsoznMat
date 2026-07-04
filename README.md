# OsoznMat

Telegram-бот для сценария «Осознанное материнство».

Стек: Python 3, aiogram 3, YAML-сценарий, SQLite, SQLAlchemy ORM, Alembic, Docker Compose. Бот работает через polling. Медиа отправляются из локальных папок `images/` и `videos/`; публичная статика и nginx не используются.

Админ-команда `/status` доступна только пользователям, перечисленным в `BOT_ADMIN_USERS`. Для остальных пользователей команда игнорируется без ответа.

## Структура

- `bot/` — код бота и движок сценария.
- `data/flow.yaml` — граф сообщений, кнопки, переходы, таймеры и ссылки.
- `data/text_issues.md` — замечания по текстам без автоматических исправлений.
- `files/guide.pdf` — PDF-гайд, который бот отправляет файлом в `КК-1`.
- `images/` — изображения для отправки.
- `images/data.txt` — описание привязки изображений к сообщениям.
- `videos/` — видеофайлы для отправки.
- `videos/data.txt` — описание привязки видео к сообщениям.
- `db/` — SQLite-база со статусами пользователей; в Docker оформлена отдельным volume.
- `tests/` — автотесты YAML, структуры данных, медиа и проверки ответа `КК-20`.

## Настройка

```bash
cp .env.sample .env
```

В `.env` нужно указать:

```env
BOT_TOKEN=123456:replace_me
BOT_ADMIN_USERS=123456789,987654321
FLOW_PATH=data/flow.yaml
DATABASE_PATH=db/bot.sqlite3
FUTURE_MESSAGES_CHECK_PERIOD=60
IMAGES_DIR=images
VIDEOS_DIR=videos
LOG_LEVEL=INFO
```

Перед первым запуском нужно создать базу:

```bash
python -m bot.main --init-db
```

Команда создаст файл SQLite, применит миграции и выведет строку `DATABASE_PATH=...`, которую нужно добавить в `.env`. Если запустить бота без существующей базы, он завершится с ошибкой и подскажет выполнить инициализацию.

`FUTURE_MESSAGES_CHECK_PERIOD` задаёт период фоновой проверки отложенных сообщений в секундах. По умолчанию используется `60`.

## Запуск локально

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m bot.main --init-db
python -m bot.main
```

## Миграции базы

Создание/обновление базы выполняется Alembic:

```bash
alembic upgrade head
```

Команда берёт путь к SQLite из `DATABASE_PATH` в `.env`. Для первого запуска удобнее использовать обёртку:

```bash
python -m bot.main --init-db
```

Отложенные переходы графа хранятся в таблице `future_messages`: `user_id`, `chat_id`, `node_id`, `source_node_id`, `send_at`, `status`, `created_at`, `sent_at`. При старте бот сразу отправляет просроченные `pending`-сообщения, затем раз в `FUTURE_MESSAGES_CHECK_PERIOD` секунд проверяет новые просроченные записи.

## Запуск через Docker Compose

```bash
docker compose up -d --build
```

При первом Docker-запуске сначала инициализируйте базу в volume:

```bash
docker compose run --rm bot python -m bot.main --init-db
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
- таймауты игнорирования: после 60 секунд молчания запускается штатный 30-секундный таймер `КК-1 → КК-17 → КК-6`, `КК-6 → КК-18 → КК-20`, `КК-20 → КК-27 → КК-28`.

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

Для Markdown-ссылок в тексте узла можно добавить:

```yaml
parse_mode: Markdown
text: |-
  Текст с [ссылкой](https://example.com/?utm_source=bot).
```

Если пользователь нажмет кнопку после запуска таймера игнорирования, состояние обновится, и отложенный автопереход не отправит дубликат.

## Важное

Тексты перенесены без редакторских исправлений. Все подозрительные места вынесены в `data/text_issues.md`.
