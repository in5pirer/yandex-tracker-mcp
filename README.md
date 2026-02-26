# yandex-tracker-mcp

MCP-сервер для работы с [Yandex Tracker API](https://tracker.yandex.ru/). Позволяет ИИ-ассистентам (Cursor, Claude Desktop и др.) управлять задачами, очередями и проектами Яндекс Трекера.

## Возможности

| Инструмент | Описание |
|---|---|
| `get_issue` | Получить задачу по ключу |
| `create_issue` | Создать задачу |
| `edit_issue` | Редактировать задачу |
| `search_issues` | Поиск задач (язык запросов Tracker) |
| `count_issues` | Подсчёт задач по запросу |
| `add_comment` | Добавить комментарий к задаче |
| `get_issue_comments` | Получить все комментарии задачи |
| `get_transitions` | Список доступных переходов статуса |
| `transition_issue` | Сменить статус задачи |
| `get_queues` | Список всех очередей |
| `get_project` | Получить проект по ID |
| `move_issue` | Переместить задачу в другую очередь |
| `link_issues` | Связать две задачи |
| `get_boards` | Список всех досок |
| `get_board` | Получить доску по ID |

## Установка

```bash
git clone https://github.com/YOUR_USERNAME/yandex-tracker-mcp.git
cd yandex-tracker-mcp
pip install -r requirements.txt
cp .env.example .env
# Заполните .env своими данными
```

## Настройка

```ini
YANDEX_TRACKER_TOKEN=your_oauth_token_here

# Yandex 360 (одно из двух):
YANDEX_TRACKER_ORG_ID=your_org_id

# Yandex Cloud:
YANDEX_TRACKER_CLOUD_ORG_ID=your_cloud_org_id
```

## Подключение к Cursor

```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "python3",
      "args": ["/path/to/yandex-tracker-mcp/src/server.py"],
      "env": {
        "YANDEX_TRACKER_TOKEN": "your_token",
        "YANDEX_TRACKER_CLOUD_ORG_ID": "your_cloud_org_id"
      }
    }
  }
}
```

## Примеры запросов (search_issues)

```
Queue: SUPPORT AND Status: Open
Assignee: me() AND Status: "In Progress"
Priority: High AND Type: Bug AND Created: > 2026-01-01
Tags: "ТСД"
Summary: ~ "ошибка"
Queue: SUPPORT ORDER BY Updated DESC
```

Документация: [Язык запросов Tracker](https://yandex.ru/support/tracker/ru/user/query-filter)

## Лицензия

MIT
