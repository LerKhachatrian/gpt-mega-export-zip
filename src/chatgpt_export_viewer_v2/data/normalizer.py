from __future__ import annotations

from typing import Dict, Iterable

from ..domain.models import ChatMessage, ThreadDetails, ThreadSummary


def to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_text(content: object) -> str:
    if not isinstance(content, dict):
        return ""

    segments: list[str] = []
    parts = content.get("parts")
    if not isinstance(parts, list):
        parts = []

    for part in parts:
        if isinstance(part, str):
            if part.strip():
                segments.append(part.strip())
            continue

        if isinstance(part, dict):
            for key in ("text", "content", "value"):
                value = part.get(key)
                if isinstance(value, str) and value.strip():
                    segments.append(value.strip())

    return "\n\n".join(segments)


def ordered_nodes(mapping: Dict[str, dict]) -> Iterable[dict]:
    if not mapping:
        return []

    children: dict[str, list[str]] = {}
    roots: list[str] = []

    for node_id, node in mapping.items():
        parent = (node or {}).get("parent")
        if parent:
            children.setdefault(str(parent), []).append(node_id)
        else:
            roots.append(node_id)

    visited: set[str] = set()
    stack = list(reversed(roots))

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)

        node = mapping.get(current)
        if isinstance(node, dict):
            yield node

        child_ids = children.get(current, [])
        for child in reversed(child_ids):
            if child not in visited:
                stack.append(child)


def build_summary(thread_obj: dict, source_file: str, is_shared: bool) -> ThreadSummary:
    thread_id = str(thread_obj.get("id") or thread_obj.get("conversation_id") or "")
    title = str(thread_obj.get("title") or "(untitled)").strip() or "(untitled)"
    created_at = to_float(thread_obj.get("create_time"))
    updated_at = to_float(thread_obj.get("update_time") or thread_obj.get("create_time"))

    mapping = thread_obj.get("mapping")
    if not isinstance(mapping, dict):
        mapping = {}

    total_messages = 0
    user_messages = 0
    assistant_messages = 0
    words = 0
    snippets: list[str] = []

    for node in ordered_nodes(mapping):
        message = node.get("message")
        if not isinstance(message, dict):
            continue

        author = message.get("author") or {}
        role = str(author.get("role") or "").lower()
        if role not in {"user", "assistant", "system"}:
            continue

        text = extract_text(message.get("content") or {})
        if not text:
            continue

        total_messages += 1
        words += len(text.split())

        if role == "user":
            user_messages += 1
        elif role == "assistant":
            assistant_messages += 1

        if len(snippets) < 2:
            snippets.append(text.replace("\n", " "))

    snippet = " // ".join(snippets)[:280]
    parse_health = "ok" if total_messages else "partial"

    return ThreadSummary(
        thread_id=thread_id,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        total_messages=total_messages,
        user_messages=user_messages,
        assistant_messages=assistant_messages,
        words=words,
        snippet=snippet,
        source_file=source_file,
        is_shared=is_shared,
        parse_health=parse_health,
    )


def build_details(thread_obj: dict, source_file: str, is_shared: bool) -> ThreadDetails:
    summary = build_summary(thread_obj, source_file=source_file, is_shared=is_shared)

    mapping = thread_obj.get("mapping")
    if not isinstance(mapping, dict):
        mapping = {}

    messages: list[ChatMessage] = []
    for node in ordered_nodes(mapping):
        message = node.get("message")
        if not isinstance(message, dict):
            continue

        author = message.get("author") or {}
        role = str(author.get("role") or "").lower()
        if role not in {"user", "assistant", "system"}:
            continue

        text = extract_text(message.get("content") or {})
        if not text:
            continue

        metadata = message.get("metadata")
        model = metadata.get("model_slug") if isinstance(metadata, dict) else None
        created = to_float(message.get("create_time") or message.get("create_time_iso"))
        msg_id = message.get("id") or message.get("message_id")

        messages.append(
            ChatMessage(
                role=role,
                content=text,
                created=created,
                model=model,
                message_id=str(msg_id) if msg_id else None,
            )
        )

    return ThreadDetails(summary=summary, messages=messages, raw=thread_obj)
