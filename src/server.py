#!/usr/bin/env python3
"""MCP server for Yandex Tracker API."""

import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from yandex_tracker_client import TrackerClient
from yandex_tracker_client.exceptions import NotFound
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

load_dotenv()

_org_id = os.getenv("YANDEX_TRACKER_ORG_ID")
_cloud_org_id = os.getenv("YANDEX_TRACKER_CLOUD_ORG_ID")

client = TrackerClient(
    token=os.getenv("YANDEX_TRACKER_TOKEN"),
    org_id=_org_id if _org_id else None,
    cloud_org_id=_cloud_org_id if _cloud_org_id else None,
)

mcp = FastMCP("yandex-tracker")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def convert_reference(ref: Any) -> Union[str, Dict[str, Any], None]:
    """Convert Yandex Tracker reference objects to readable format."""
    if ref is None:
        return None
    if isinstance(ref, (str, int, float, bool)):
        return ref
    if isinstance(ref, datetime):
        return ref.isoformat()
    if isinstance(ref, list):
        return [convert_reference(item) for item in ref]
    try:
        if hasattr(ref, "display"):
            return {
                "id": getattr(ref, "id", None),
                "key": getattr(ref, "key", None),
                "display": ref.display,
            }
        return str(ref)
    except Exception:
        return str(ref)


def format_issue(issue: Any) -> Dict[str, Any]:
    """Format issue object to readable dictionary."""
    return {
        "key": issue.key,
        "summary": issue.summary,
        "description": issue.description,
        "status": convert_reference(issue.status),
        "assignee": convert_reference(issue.assignee),
        "created_at": convert_reference(issue.createdAt),
        "updated_at": convert_reference(issue.updatedAt),
        "deadline": convert_reference(getattr(issue, "deadline", None)),
        "priority": convert_reference(issue.priority),
        "type": convert_reference(issue.type),
        "queue": convert_reference(issue.queue),
        "tags": convert_reference(getattr(issue, "tags", None)),
        "components": convert_reference(getattr(issue, "components", None)),
        "sprint": convert_reference(getattr(issue, "sprint", None)),
        "story_points": getattr(issue, "storyPoints", None),
        "parent": convert_reference(getattr(issue, "parent", None)),
    }


def _raw_get(path: str, params: dict = None) -> Any:
    return client._connection.get(path=path, params=params or {})


def _raw_post(path: str, data: dict = None) -> Any:
    return client._connection.post(path=path, data=data or {})


def _raw_patch(path: str, data: dict = None) -> Any:
    return client._connection.patch(path=path, data=data or {})


# ─── Queues ───────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_queues() -> dict:
    """Get all available queues in Yandex Tracker.

    Returns:
        List of queues with their keys, names and descriptions
    """
    try:
        response = _raw_get("/v2/queues")
        queues = list(response) if response else []
        result = []
        for q in queues:
            if hasattr(q, "get"):
                result.append({"key": q.get("key"), "name": q.get("name"), "description": q.get("description")})
            else:
                result.append({
                    "key": getattr(q, "key", None),
                    "name": getattr(q, "name", None),
                    "description": getattr(q, "description", None),
                })
        return {"queues": result, "total": len(result)}
    except Exception as e:
        return {"error": f"Failed to get queues: {e}"}


@mcp.tool()
async def get_queue(queue_key: str) -> dict:
    """Get details of a specific queue.

    Args:
        queue_key: Queue key, e.g. "SUPPORT"
    """
    try:
        response = _raw_get(f"/v2/queues/{queue_key}")
        if hasattr(response, "get"):
            return dict(response)
        return {
            "key": getattr(response, "key", None),
            "name": getattr(response, "name", None),
            "description": getattr(response, "description", None),
            "lead": convert_reference(getattr(response, "lead", None)),
            "defaultPriority": convert_reference(getattr(response, "defaultPriority", None)),
        }
    except Exception as e:
        return {"error": f"Failed to get queue {queue_key}: {e}"}


@mcp.tool()
async def get_queue_components(queue_key: str) -> dict:
    """Get all components of a queue.

    Args:
        queue_key: Queue key, e.g. "SUPPORT"

    Returns:
        List of components with id and name
    """
    try:
        response = _raw_get(f"/v2/queues/{queue_key}/components")
        components = list(response) if response else []
        result = [
            {
                "id": getattr(c, "id", None) if not hasattr(c, "get") else c.get("id"),
                "name": getattr(c, "name", None) if not hasattr(c, "get") else c.get("name"),
                "description": getattr(c, "description", None) if not hasattr(c, "get") else c.get("description"),
            }
            for c in components
        ]
        return {"queue": queue_key, "components": result, "total": len(result)}
    except Exception as e:
        return {"error": f"Failed to get components for {queue_key}: {e}"}


@mcp.tool()
async def create_component(queue_key: str, name: str, description: str = None, assignee: str = None) -> dict:
    """Create a new component in a queue.

    Args:
        queue_key: Queue key, e.g. "SUPPORT"
        name: Component name
        description: Optional description
        assignee: Optional default assignee login
    """
    try:
        data: dict = {"name": name, "queue": queue_key}
        if description:
            data["description"] = description
        if assignee:
            data["assignee"] = assignee
        response = _raw_post("/v2/components", data=data)
        return {
            "id": getattr(response, "id", None),
            "name": getattr(response, "name", name),
            "queue": queue_key,
        }
    except Exception as e:
        return {"error": f"Failed to create component: {e}"}


# ─── Users ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_users() -> dict:
    """Get list of users in the organization.

    Returns:
        List of users with login, display name and email
    """
    try:
        response = _raw_get("/v2/users")
        users = list(response) if response else []
        result = []
        for u in users:
            if hasattr(u, "get"):
                result.append({"login": u.get("login"), "display": u.get("display"), "email": u.get("email")})
            else:
                result.append({
                    "login": getattr(u, "login", None),
                    "display": getattr(u, "display", None),
                    "email": getattr(u, "email", None),
                })
        return {"users": result, "total": len(result)}
    except Exception as e:
        return {"error": f"Failed to get users: {e}"}


@mcp.tool()
async def get_myself() -> dict:
    """Get information about the currently authenticated user."""
    try:
        response = _raw_get("/v2/myself")
        if hasattr(response, "get"):
            return dict(response)
        return {
            "login": getattr(response, "login", None),
            "display": getattr(response, "display", None),
            "email": getattr(response, "email", None),
        }
    except Exception as e:
        return {"error": f"Failed to get myself: {e}"}


# ─── Issues CRUD ──────────────────────────────────────────────────────────────

@mcp.tool()
async def get_issue(issue_id: str) -> dict:
    """Get issue details from Yandex Tracker by issue key.

    Args:
        issue_id: Issue key, e.g. "SUPPORT-123"
    """
    try:
        issue = client.issues[issue_id]
        return format_issue(issue)
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to get issue: {e}"}


@mcp.tool()
async def create_issue(
    queue: str,
    summary: str,
    description: Optional[str] = None,
    type: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    deadline: Optional[str] = None,
    tags: Optional[List[str]] = None,
    components: Optional[List[str]] = None,
    parent: Optional[str] = None,
    sprint: Optional[str] = None,
) -> dict:
    """Create a new issue in Yandex Tracker.

    Args:
        queue: Queue key where the issue will be created (e.g. "SUPPORT")
        summary: Issue title
        description: Optional issue description (Markdown supported)
        type: Optional issue type (e.g. "task", "bug", "improvement")
        priority: Optional priority ("blocker", "critical", "major", "normal", "minor", "trivial")
        assignee: Optional assignee login
        deadline: Optional deadline in ISO format (e.g. "2026-03-31")
        tags: Optional list of tags
        components: Optional list of component names
        parent: Optional parent issue key (for subtasks)
        sprint: Optional sprint ID
    """
    try:
        kwargs: dict = {"queue": queue, "summary": summary}
        if description:
            kwargs["description"] = description
        if type:
            kwargs["type"] = type
        if priority:
            kwargs["priority"] = priority
        if assignee:
            kwargs["assignee"] = assignee
        if deadline:
            kwargs["deadline"] = deadline
        if tags:
            kwargs["tags"] = tags
        if components:
            kwargs["components"] = components
        if parent:
            kwargs["parent"] = parent
        if sprint:
            kwargs["sprint"] = sprint
        issue = client.issues.create(**kwargs)
        return format_issue(issue)
    except Exception as e:
        return {"error": f"Failed to create issue: {e}"}


@mcp.tool()
async def edit_issue(
    issue_id: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    type: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    deadline: Optional[str] = None,
    tags: Optional[List[str]] = None,
    components: Optional[List[str]] = None,
) -> dict:
    """Edit an existing issue in Yandex Tracker.

    Args:
        issue_id: Issue key to edit (e.g. "SUPPORT-123")
        summary: New summary (optional)
        description: New description (optional)
        type: New type (optional)
        priority: New priority (optional)
        assignee: New assignee login (optional)
        deadline: New deadline in ISO format (optional)
        tags: New tags list (optional, replaces existing tags)
        components: New components list (optional)
    """
    try:
        issue = client.issues[issue_id]
        if summary:
            issue.summary = summary
        if description:
            issue.description = description
        if type:
            issue.type = type
        if priority:
            issue.priority = priority
        if assignee:
            issue.assignee = assignee
        if deadline:
            issue.deadline = deadline
        if tags is not None:
            issue.tags = tags
        if components is not None:
            issue.components = components
        issue.save()
        return format_issue(issue)
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to edit issue: {e}"}


@mcp.tool()
async def bulk_update_issues(issue_ids: List[str], fields: Dict[str, Any]) -> dict:
    """Update multiple issues at once with the same field values.

    Args:
        issue_ids: List of issue keys, e.g. ["SUPPORT-1", "SUPPORT-2"]
        fields: Dictionary of fields to update, e.g. {"priority": "major", "assignee": "user1"}

    Returns:
        Summary of updated issues
    """
    try:
        updated = []
        failed = []
        for issue_id in issue_ids:
            try:
                issue = client.issues[issue_id]
                for field, value in fields.items():
                    setattr(issue, field, value)
                issue.save()
                updated.append(issue_id)
            except Exception as e:
                failed.append({"issue": issue_id, "error": str(e)})
        return {"updated": updated, "failed": failed, "total_updated": len(updated), "total_failed": len(failed)}
    except Exception as e:
        return {"error": f"Bulk update failed: {e}"}


@mcp.tool()
async def move_issue(issue_id: str, queue: str) -> dict:
    """Move an issue to a different queue.

    Args:
        issue_id: Issue key to move
        queue: Target queue key
    """
    try:
        issue = client.issues[issue_id]
        issue.move(queue)
        return format_issue(issue)
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to move issue: {e}"}


# ─── Search ───────────────────────────────────────────────────────────────────

@mcp.tool()
async def search_issues(
    query: str,
    per_page: Optional[int] = 50,
    page: Optional[int] = 1,
) -> dict:
    """Search for issues using Yandex Tracker query language.

    Query examples:
        Queue: SUPPORT AND Status: Open
        Assignee: me() AND Status: "In Progress"
        Priority: High AND Type: Bug AND Created: > 2026-01-01
        Tags: "ТСД"
        Summary: ~ "ошибка"
        Queue: SUPPORT ORDER BY Updated DESC

    See: https://yandex.ru/support/tracker/ru/user/query-filter#filter-parameters

    Args:
        query: Search query in Yandex Tracker query language
        per_page: Number of issues per page (default: 50)
        page: Page number (default: 1)
    """
    try:
        issues = client.issues.find(query, per_page=per_page, page=page)
        return {
            "issues": [format_issue(issue) for issue in issues],
            "total": len(issues),
        }
    except Exception as e:
        return {"error": f"Failed to search issues: {e}"}


@mcp.tool()
async def count_issues(query: str) -> dict:
    """Count issues matching the query without fetching all data.

    Args:
        query: Query string in Yandex Tracker query language
    """
    try:
        response = _raw_post("/v3/issues/_count", data={"query": query})
        return {"count": response}
    except Exception as e:
        return {"error": f"Failed to count issues: {e}"}


# ─── Comments ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_issue_comments(issue_id: str) -> dict:
    """Get all comments for a given issue.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
    """
    try:
        response = _raw_get(f"/v2/issues/{issue_id}/comments", params={"expand": "all"})
        comments_list = list(response) if response else []
        comments_data = []
        for comment in comments_list:
            if hasattr(comment, "get"):
                author_info = comment.get("createdBy", {})
                author_display = author_info.get("display", "Unknown") if isinstance(author_info, dict) else str(author_info)
                comments_data.append({
                    "id": comment.get("id"),
                    "text": comment.get("text", ""),
                    "author": author_display,
                    "created_at": comment.get("createdAt"),
                    "updated_at": comment.get("updatedAt"),
                })
            else:
                author_info = getattr(comment, "createdBy", {})
                author_display = author_info.get("display", "Unknown") if isinstance(author_info, dict) else str(author_info)
                comments_data.append({
                    "id": getattr(comment, "id", None),
                    "text": getattr(comment, "text", ""),
                    "author": author_display,
                    "created_at": getattr(comment, "createdAt", None),
                    "updated_at": getattr(comment, "updatedAt", None),
                })
        return {"issue_id": issue_id, "comments": comments_data, "total": len(comments_data)}
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to get comments: {e}"}


@mcp.tool()
async def add_comment(issue_id: str, text: str) -> dict:
    """Add a comment to an issue.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
        text: Comment text (Markdown supported)
    """
    try:
        issue = client.issues[issue_id]
        comment = issue.comments.create(text=text)
        return {
            "id": getattr(comment, "id", None),
            "text": getattr(comment, "text", text),
            "created_at": convert_reference(getattr(comment, "createdAt", None)),
            "author": convert_reference(getattr(comment, "createdBy", None)),
        }
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to add comment: {e}"}


# ─── Status transitions ───────────────────────────────────────────────────────

@mcp.tool()
async def get_transitions(issue_id: str) -> dict:
    """Get available status transitions for an issue.
    Use this before transition_issue to find valid transition IDs.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
    """
    try:
        issue = client.issues[issue_id]
        transitions = issue.transitions.get_all()
        result = []
        for t in transitions:
            result.append({
                "id": getattr(t, "id", None),
                "display": getattr(t, "display", None),
                "to": convert_reference(getattr(t, "to", None)),
            })
        return {"issue_id": issue_id, "transitions": result}
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to get transitions: {e}"}


@mcp.tool()
async def transition_issue(
    issue_id: str,
    transition_id: str,
    comment: Optional[str] = None,
    resolution: Optional[str] = None,
) -> dict:
    """Change issue status via a transition.
    Use get_transitions first to find valid transition IDs.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
        transition_id: Transition ID (from get_transitions)
        comment: Optional comment to add during the transition
        resolution: Optional resolution key for closing transitions (e.g. "fixed", "wontFix", "duplicate", "cantReproduce")
    """
    try:
        issue = client.issues[issue_id]
        transition = issue.transitions[transition_id]
        kwargs: Dict[str, Any] = {}
        if comment:
            kwargs["comment"] = comment
        if resolution:
            kwargs["resolution"] = resolution
        transition.execute(**kwargs)
        return format_issue(client.issues[issue_id])
    except NotFound:
        return {"error": f"Issue {issue_id} or transition {transition_id} not found"}
    except Exception as e:
        return {"error": f"Failed to execute transition: {e}"}


# ─── Links ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_issue_links(issue_id: str) -> dict:
    """Get all links (relations) for an issue.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")

    Returns:
        List of linked issues with type and direction
    """
    try:
        response = _raw_get(f"/v2/issues/{issue_id}/links")
        links = list(response) if response else []
        result = []
        for link in links:
            if hasattr(link, "get"):
                result.append({
                    "type": link.get("type", {}).get("id") if isinstance(link.get("type"), dict) else link.get("type"),
                    "direction": link.get("direction"),
                    "object": link.get("object", {}).get("key") if isinstance(link.get("object"), dict) else link.get("object"),
                })
            else:
                link_type = getattr(link, "type", None)
                link_obj = getattr(link, "object", None)
                result.append({
                    "type": getattr(link_type, "id", str(link_type)) if link_type else None,
                    "direction": getattr(link, "direction", None),
                    "object": getattr(link_obj, "key", str(link_obj)) if link_obj else None,
                })
        return {"issue_id": issue_id, "links": result, "total": len(result)}
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to get links: {e}"}


@mcp.tool()
async def link_issues(source_issue: str, target_issue: str, link_type: str) -> dict:
    """Link two issues together.

    Args:
        source_issue: Source issue key
        target_issue: Target issue key
        link_type: Type of link ("relates", "blocks", "depends", "duplicates", "subtask")
    """
    try:
        source = client.issues[source_issue]
        target = client.issues[target_issue]
        source.link(target, link_type)
        return {"success": True, "source": source_issue, "target": target_issue, "type": link_type}
    except NotFound as e:
        return {"error": f"Issue not found: {e}"}
    except Exception as e:
        return {"error": f"Failed to link issues: {e}"}


# ─── Attachments ──────────────────────────────────────────────────────────────

@mcp.tool()
async def get_attachments(issue_id: str) -> dict:
    """Get list of files attached to an issue.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
    """
    try:
        response = _raw_get(f"/v2/issues/{issue_id}/attachments")
        files = list(response) if response else []
        result = []
        for f in files:
            if hasattr(f, "get"):
                result.append({"id": f.get("id"), "name": f.get("name"), "url": f.get("download")})
            else:
                result.append({
                    "id": getattr(f, "id", None),
                    "name": getattr(f, "name", None),
                    "url": getattr(f, "download", None),
                })
        return {"issue_id": issue_id, "attachments": result, "total": len(result)}
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to get attachments: {e}"}


# ─── Worklog (time tracking) ──────────────────────────────────────────────────

@mcp.tool()
async def get_worklog(issue_id: str) -> dict:
    """Get time tracking records (worklog) for an issue.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
    """
    try:
        response = _raw_get(f"/v2/issues/{issue_id}/worklog")
        records = list(response) if response else []
        result = []
        for r in records:
            if hasattr(r, "get"):
                result.append({
                    "id": r.get("id"),
                    "author": r.get("createdBy", {}).get("display") if isinstance(r.get("createdBy"), dict) else r.get("createdBy"),
                    "duration": r.get("duration"),
                    "date": r.get("start"),
                    "comment": r.get("comment"),
                })
            else:
                created_by = getattr(r, "createdBy", None)
                result.append({
                    "id": getattr(r, "id", None),
                    "author": created_by.get("display") if isinstance(created_by, dict) else str(created_by) if created_by else None,
                    "duration": getattr(r, "duration", None),
                    "date": getattr(r, "start", None),
                    "comment": getattr(r, "comment", None),
                })
        return {"issue_id": issue_id, "worklog": result, "total": len(result)}
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to get worklog: {e}"}


@mcp.tool()
async def add_worklog(issue_id: str, duration: str, comment: Optional[str] = None, date: Optional[str] = None) -> dict:
    """Add a time tracking record to an issue.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
        duration: Time spent in ISO 8601 duration format (e.g. "PT2H30M" = 2h 30min, "P1D" = 1 day)
        comment: Optional comment for this worklog entry
        date: Optional date in ISO format (e.g. "2026-03-15"), defaults to today
    """
    try:
        data: dict = {"duration": duration}
        if comment:
            data["comment"] = comment
        if date:
            data["start"] = date
        response = _raw_post(f"/v2/issues/{issue_id}/worklog", data=data)
        return {
            "success": True,
            "id": getattr(response, "id", None) if not hasattr(response, "get") else response.get("id"),
            "duration": duration,
            "issue_id": issue_id,
        }
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to add worklog: {e}"}


# ─── Checklists ───────────────────────────────────────────────────────────────

@mcp.tool()
async def get_checklist(issue_id: str) -> dict:
    """Get checklist items of an issue.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
    """
    try:
        response = _raw_get(f"/v2/issues/{issue_id}/checklistItems")
        items = list(response) if response else []
        result = []
        for item in items:
            if hasattr(item, "get"):
                result.append({"id": item.get("id"), "text": item.get("text"), "checked": item.get("checked", False)})
            else:
                result.append({
                    "id": getattr(item, "id", None),
                    "text": getattr(item, "text", None),
                    "checked": getattr(item, "checked", False),
                })
        return {"issue_id": issue_id, "items": result, "total": len(result), "done": sum(1 for i in result if i["checked"])}
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to get checklist: {e}"}


@mcp.tool()
async def add_checklist_item(issue_id: str, text: str, checked: bool = False) -> dict:
    """Add an item to an issue checklist.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
        text: Checklist item text
        checked: Initial checked state (default False)
    """
    try:
        data = {"text": text, "checked": checked}
        response = _raw_post(f"/v2/issues/{issue_id}/checklistItems", data=data)
        return {
            "success": True,
            "id": getattr(response, "id", None) if not hasattr(response, "get") else response.get("id"),
            "text": text,
            "checked": checked,
        }
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to add checklist item: {e}"}


@mcp.tool()
async def update_checklist_item(issue_id: str, item_id: str, text: Optional[str] = None, checked: Optional[bool] = None) -> dict:
    """Update a checklist item (mark as done or edit text).

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
        item_id: Checklist item ID (from get_checklist)
        text: New text (optional)
        checked: New checked state (optional)
    """
    try:
        data: dict = {}
        if text is not None:
            data["text"] = text
        if checked is not None:
            data["checked"] = checked
        _raw_patch(f"/v2/issues/{issue_id}/checklistItems/{item_id}", data=data)
        return {"success": True, "item_id": item_id, "issue_id": issue_id}
    except NotFound:
        return {"error": f"Issue {issue_id} or item {item_id} not found"}
    except Exception as e:
        return {"error": f"Failed to update checklist item: {e}"}


# ─── Boards & Sprints ─────────────────────────────────────────────────────────

@mcp.tool()
async def get_boards() -> dict:
    """Get all agile boards from Yandex Tracker."""
    try:
        response = _raw_get("/v3/boards")
        return {"boards": list(response) if response else [], "total": len(response) if response else 0}
    except Exception as e:
        return {"error": f"Failed to get boards: {e}"}


@mcp.tool()
async def get_board(board_id: str) -> dict:
    """Get a specific agile board.

    Args:
        board_id: Board ID
    """
    try:
        return _raw_get(f"/v3/boards/{board_id}")
    except Exception as e:
        return {"error": f"Failed to get board: {e}"}


@mcp.tool()
async def get_board_sprints(board_id: str) -> dict:
    """Get all sprints for an agile board.

    Args:
        board_id: Board ID (from get_boards)

    Returns:
        List of sprints with id, name, start/end dates and status
    """
    try:
        response = _raw_get(f"/v3/boards/{board_id}/sprints")
        sprints = list(response) if response else []
        result = []
        for s in sprints:
            if hasattr(s, "get"):
                result.append({"id": s.get("id"), "name": s.get("name"), "status": s.get("status"), "startDate": s.get("startDate"), "endDate": s.get("endDate")})
            else:
                result.append({
                    "id": getattr(s, "id", None),
                    "name": getattr(s, "name", None),
                    "status": getattr(s, "status", None),
                    "startDate": getattr(s, "startDate", None),
                    "endDate": getattr(s, "endDate", None),
                })
        return {"board_id": board_id, "sprints": result, "total": len(result)}
    except Exception as e:
        return {"error": f"Failed to get sprints for board {board_id}: {e}"}


@mcp.tool()
async def create_sprint(board_id: str, name: str, start_date: str, end_date: str) -> dict:
    """Create a new sprint on an agile board.

    Args:
        board_id: Board ID
        name: Sprint name
        start_date: Start date in ISO format (e.g. "2026-03-01")
        end_date: End date in ISO format (e.g. "2026-03-14")
    """
    try:
        data = {"name": name, "board": {"id": board_id}, "startDate": start_date, "endDate": end_date}
        response = _raw_post("/v3/sprints", data=data)
        if hasattr(response, "get"):
            return {"success": True, "id": response.get("id"), "name": response.get("name")}
        return {"success": True, "id": getattr(response, "id", None), "name": getattr(response, "name", name)}
    except Exception as e:
        return {"error": f"Failed to create sprint: {e}"}


@mcp.tool()
async def get_sprint_issues(sprint_id: str) -> dict:
    """Get all issues in a sprint.

    Args:
        sprint_id: Sprint ID (from get_board_sprints)
    """
    try:
        issues = client.issues.find(f"Sprint: {sprint_id}")
        return {
            "sprint_id": sprint_id,
            "issues": [format_issue(i) for i in issues],
            "total": len(issues),
        }
    except Exception as e:
        return {"error": f"Failed to get sprint issues: {e}"}


# ─── Changelog ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_issue_changelog(
    issue_id: str,
    field: Optional[str] = None,
    per_page: Optional[int] = 50,
) -> dict:
    """Get the full changelog (history of field changes) for an issue.

    Useful for tracking status transitions, assignee changes, priority changes, etc.
    Each entry shows who changed what field, from which value to which value, and when.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
        field: Optional field name to filter by (e.g. "status", "assignee", "priority").
               If not specified, returns changes for all fields.
        per_page: Number of changelog entries per page (default: 50)
    """
    try:
        params: dict = {"perPage": per_page}
        if field:
            params["field"] = field

        all_entries = []
        last_id = None

        while True:
            if last_id:
                params["id"] = last_id
            response = _raw_get(f"/v2/issues/{issue_id}/changelog", params=params)
            entries = list(response) if response else []
            if not entries:
                break

            for entry in entries:
                e_id = getattr(entry, "id", None)
                updated_at = getattr(entry, "updatedAt", None)
                updated_by = getattr(entry, "updatedBy", None)
                change_type = getattr(entry, "type", None)

                fields_changed = []
                for fc in getattr(entry, "fields", []):
                    f_ref = fc.get("field") if isinstance(fc, dict) else None
                    from_ref = fc.get("from") if isinstance(fc, dict) else None
                    to_ref = fc.get("to") if isinstance(fc, dict) else None

                    f_id = convert_reference(f_ref) if f_ref else None
                    from_val = convert_reference(from_ref)
                    to_val = convert_reference(to_ref)

                    if isinstance(f_id, dict):
                        field_id = f_id.get("key") or f_id.get("id")
                        field_name = f_id.get("display")
                    elif isinstance(f_id, str):
                        field_id = f_id
                        field_name = f_id
                    else:
                        field_id = None
                        field_name = None

                    def _display(val: Any) -> Any:
                        if isinstance(val, dict):
                            return val.get("display", val.get("key", str(val)))
                        return val

                    fields_changed.append({
                        "field_id": field_id,
                        "field_name": field_name,
                        "from": _display(from_val),
                        "to": _display(to_val),
                    })

                all_entries.append({
                    "id": e_id,
                    "updated_at": updated_at,
                    "author": convert_reference(updated_by),
                    "type": change_type,
                    "fields": fields_changed,
                })

            if len(entries) < per_page:
                break
            last_id = all_entries[-1]["id"]

        return {
            "issue_id": issue_id,
            "changelog": all_entries,
            "total": len(all_entries),
        }
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to get changelog: {e}"}


# ─── Projects ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_project(project_id: str) -> dict:
    """Get project details from Yandex Tracker.

    Args:
        project_id: Project ID to retrieve
    """
    try:
        project = client.projects.get(project_id)
        return {
            "id": project.id,
            "key": project.key,
            "name": project.name,
            "description": getattr(project, "description", None),
            "lead": convert_reference(project.lead),
            "status": getattr(project, "status", None),
            "startDate": getattr(project, "startDate", None),
            "endDate": getattr(project, "endDate", None),
        }
    except NotFound:
        return {"error": f"Project {project_id} not found"}
    except Exception as e:
        return {"error": f"Failed to get project: {e}"}


if __name__ == "__main__":
    mcp.run()
