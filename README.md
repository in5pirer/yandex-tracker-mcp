# yandex-tracker-mcp

MCP-сервер для работы с [Yandex Tracker API](https://tracker.yandex.ru/). Позволяет ИИ-ассистентам (Cursor, Claude Desktop и др.) управлять задачами, очередями, спринтами, чек-листами, учётом времени и пользователями.

## Инструменты — 31 штук

### Задачи

| Инструмент | Описание |
|---|---|
| `get_issue` | Получить задачу по ключу (QUEUE-123) |
| `create_issue` | Создать задачу (очередь, название, описание, приоритет, тип, исполнитель, дедлайн, теги, компоненты, родитель, спринт) |
| `edit_issue` | Редактировать задачу |
| `move_issue` | Переместить задачу в другую очередь |
| `bulk_update_issues` | Массовое обновление нескольких задач одновременно |

### Поиск

| Инструмент | Описание |
|---|---|
| `search_issues` | Поиск задач на языке запросов Tracker с пагинацией |
| `count_issues` | Подсчёт задач по запросу без загрузки данных |

### Комментарии

| Инструмент | Описание |
|---|---|
| `get_issue_comments` | Все комментарии задачи |
| `add_comment` | Добавить комментарий к задаче (Markdown) |

### Статусы и переходы

| Инструмент | Описание |
|---|---|
| `get_transitions` | Список доступных переходов статуса для задачи |
| `transition_issue` | Сменить статус задачи через переход (поддерживает резолюцию при закрытии) |

### Связи между задачами

| Инструмент | Описание |
|---|---|
| `get_issue_links` | Все связи задачи с другими задачами |
| `link_issues` | Связать две задачи (relates, blocks, depends, duplicates, subtask) |

### Вложения

| Инструмент | Описание |
|---|---|
| `get_attachments` | Список файлов, прикреплённых к задаче |

### Учёт времени (Worklog)

| Инструмент | Описание |
|---|---|
| `get_worklog` | Записи о затраченном времени по задаче |
| `add_worklog` | Добавить запись о времени (ISO 8601: PT2H30M, P1D) |

### Чек-листы

| Инструмент | Описание |
|---|---|
| `get_checklist` | Чек-лист задачи с прогрессом выполнения |
| `add_checklist_item` | Добавить пункт в чек-лист |
| `update_checklist_item` | Изменить текст или отметить пункт выполненным |

### Очереди и компоненты

| Инструмент | Описание |
|---|---|
| `get_queues` | Список всех очередей организации |
| `get_queue` | Детали конкретной очереди |
| `get_queue_components` | Компоненты очереди |
| `create_component` | Создать новый компонент в очереди |

### Пользователи

| Инструмент | Описание |
|---|---|
| `get_users` | Список пользователей организации |
| `get_myself` | Информация об авторизованном пользователе |

### Доски и спринты

| Инструмент | Описание |
|---|---|
| `get_boards` | Список всех досок |
| `get_board` | Детали конкретной доски |
| `get_board_sprints` | Все спринты доски со статусами и датами |
| `create_sprint` | Создать новый спринт на доске |
| `get_sprint_issues` | Все задачи спринта |

### Проекты

| Инструмент | Описание |
|---|---|
| `get_project` | Получить проект по ID |

## Установка

```bash
git clone https://github.com/in5pirer/yandex-tracker-mcp.git
cd yandex-tracker-mcp
pip install -r requirements.txt
cp .env.example .env
# Заполните .env своими данными
```

## Настройка

```ini
# OAuth-токен из https://oauth.yandex.ru/
YANDEX_TRACKER_TOKEN=your_oauth_token_here

# Для Yandex 360:
YANDEX_TRACKER_ORG_ID=your_org_id

# Для Yandex Cloud (используйте одно из двух):
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

> После изменения `server.py` необходимо перезапустить Cursor.

## Примеры запросов (search_issues)

```
Queue: SUPPORT AND Status: Open
Assignee: me() AND Status: "In Progress"
Priority: High AND Type: Bug AND Created: > 2026-01-01
Tags: "ТСД"
Summary: ~ "ошибка"
Queue: SUPPORT ORDER BY Updated DESC
Sprint: 123
```

Документация: [Язык запросов Tracker](https://yandex.ru/support/tracker/ru/user/query-filter)

## Примеры использования

**Создать задачу с дедлайном и тегами:**
```
create_issue(queue="SUPPORT", summary="Исправить ошибку", priority="critical",
             assignee="user1", deadline="2026-03-31", tags=["баг", "срочно"])
```

**Закрыть задачу с резолюцией:**
```
transition_issue(issue_id="SUPPORT-123", transition_id="close",
                 resolution="fixed", comment="Задача выполнена")
```

Доступные резолюции: `fixed`, `wontFix`, `duplicate`, `cantReproduce`.

**Массово обновить задачи:**
```
bulk_update_issues(issue_ids=["SUPPORT-1", "SUPPORT-2"], fields={"assignee": "user2"})
```

**Добавить время на задачу:**
```
add_worklog(issue_id="SUPPORT-123", duration="PT2H30M", comment="Анализ проблемы")
```

## Лицензия

MIT
