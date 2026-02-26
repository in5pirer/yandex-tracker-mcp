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


@mcp.tool()
async def get_queues() -> dict:
    """Get all available queues in Yandex Tracker.

    Returns:
        List of queues with their keys and names
    """
    try:
        response = client._connection.get(path="/v2/queues")
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
        return {"error": f"Failed to get queues: {str(e)}"}


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
            "version": project.version,
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
        return {"error": f"Failed to get project: {str(e)}"}


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
        return {"error": f"Failed to get issue: {str(e)}"}


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
    parent: Optional[str] = None,
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
        parent: Optional parent issue key (for subtasks)
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
        if parent:
            kwargs["parent"] = parent
        issue = client.issues.create(**kwargs)
        return format_issue(issue)
    except Exception as e:
        return {"error": f"Failed to create issue: {str(e)}"}


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
        issue.save()
        return format_issue(issue)
    except NotFound:
        return {"error": f"Issue {issue_id} not found"}
    except Exception as e:
        return {"error": f"Failed to edit issue: {str(e)}"}


@mcp.tool()
async def add_comment(issue_id: str, text: str) -> dict:
    """Add a comment to an issue in Yandex Tracker.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
        text: Comment text (Markdown supported)

    Returns:
        Created comment data
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
        return {"error": f"Failed to add comment: {str(e)}"}


@mcp.tool()
async def get_transitions(issue_id: str) -> dict:
    """Get available status transitions for an issue.
    Use this before calling transition_issue to find valid transition IDs.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")

    Returns:
        List of available transitions with id and target status name
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
        return {"error": f"Failed to get transitions: {str(e)}"}


@mcp.tool()
async def transition_issue(issue_id: str, transition_id: str, comment: Optional[str] = None) -> dict:
    """Change issue status via a transition.
    Use get_transitions first to find valid transition IDs.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
        transition_id: Transition ID (from get_transitions)
        comment: Optional comment to add during the transition

    Returns:
        Updated issue data
    """
    try:
        issue = client.issues[issue_id]
        transition = issue.transitions[transition_id]
        kwargs = {}
        if comment:
            kwargs["comment"] = comment
        transition.execute(**kwargs)
        return format_issue(client.issues[issue_id])
    except NotFound:
        return {"error": f"Issue {issue_id} or transition {transition_id} not found"}
    except Exception as e:
        return {"error": f"Failed to execute transition: {str(e)}"}


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
        return {"error": f"Failed to move issue: {str(e)}"}


@mcp.tool()
async def count_issues(query: str) -> dict:
    """Count issues in Yandex Tracker matching the query.

    Args:
        query: Query string in Yandex Tracker query language
    """
    try:
        response = client._connection.post(
            path="/v3/issues/_count",
            data={"query": query},
        )
        return {"count": response}
    except Exception as e:
        return {"error": f"Failed to count issues: {str(e)}"}


@mcp.tool()
async def search_issues(
    query: str,
    per_page: Optional[int] = 50,
    page: Optional[int] = 1,
) -> dict:
    """
    Search for issues using Yandex Tracker query language.

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

    Returns:
        Dictionary with 'issues' list and 'total' count
    """
    try:
        issues = client.issues.find(query, per_page=per_page, page=page)
        return {
            "issues": [format_issue(issue) for issue in issues],
            "total": len(issues),
        }
    except Exception as e:
        return {"error": f"Failed to search issues: {str(e)}"}


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
        return {
            "source": format_issue(source),
            "target": format_issue(target),
            "link_type": link_type,
        }
    except NotFound as e:
        return {"error": f"Issue not found: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to link issues: {str(e)}"}


@mcp.tool()
async def get_issue_comments(issue_id: str) -> dict:
    """Get all comments for a given issue in Yandex Tracker.

    Args:
        issue_id: Issue key (e.g. "SUPPORT-123")
    """
    try:
        response = client._connection.get(
            path=f"/v2/issues/{issue_id}/comments",
            params={"expand": "all"},
        )
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
        return {"error": f"Failed to get comments: {str(e)}"}


@mcp.tool()
async def get_boards() -> dict:
    """Get all boards from Yandex Tracker."""
    try:
        response = client._connection.get(path="/v3/boards")
        return {"boards": response, "total": len(response) if response else 0}
    except Exception as e:
        return {"error": f"Failed to get boards: {str(e)}"}


@mcp.tool()
async def get_board(board_id: str) -> dict:
    """Get a specific board from Yandex Tracker.

    Args:
        board_id: Board ID to retrieve
    """
    try:
        response = client._connection.get(path=f"/v3/boards/{board_id}")
        return response
    except Exception as e:
        return {"error": f"Failed to get board: {str(e)}"}


if __name__ == "__main__":
    mcp.run()
