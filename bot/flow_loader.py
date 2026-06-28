from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Flow:
    start: str
    nodes: dict[str, dict[str, Any]]

    def get(self, node_id: str) -> dict[str, Any]:
        try:
            return self.nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"Unknown flow node: {node_id}") from exc


def load_flow(path: Path) -> Flow:
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if not isinstance(raw, dict):
        raise ValueError("Flow YAML root must be a mapping")
    start = raw.get("start")
    nodes = raw.get("nodes")
    if not isinstance(start, str):
        raise ValueError("Flow YAML must contain string 'start'")
    if not isinstance(nodes, dict):
        raise ValueError("Flow YAML must contain mapping 'nodes'")
    return Flow(start=start, nodes=nodes)


def validate_flow(flow: Flow) -> list[str]:
    errors: list[str] = []
    if flow.start not in flow.nodes:
        errors.append(f"start points to missing node {flow.start!r}")

    for node_id, node in flow.nodes.items():
        if not isinstance(node, dict):
            errors.append(f"{node_id}: node must be a mapping")
            continue
        if node.get("id") != node_id:
            errors.append(f"{node_id}: id field must match node key")
        if node.get("type") != "timer" and "text" not in node and "media" not in node:
            errors.append(f"{node_id}: node must contain text or media")

        buttons = node.get("buttons", [])
        if buttons is not None and not isinstance(buttons, list):
            errors.append(f"{node_id}: buttons must be a list")
        for index, button in enumerate(buttons or []):
            if not isinstance(button, dict):
                errors.append(f"{node_id}: button #{index + 1} must be a mapping")
                continue
            if not isinstance(button.get("text"), str):
                errors.append(f"{node_id}: button #{index + 1} must contain text")
            target = button.get("target")
            url = button.get("url")
            if target and target not in flow.nodes:
                errors.append(f"{node_id}: button #{index + 1} targets missing node {target!r}")
            if not target and not url:
                errors.append(f"{node_id}: button #{index + 1} must contain target or url")

        for field in ("next", "fallback"):
            target = node.get(field)
            if isinstance(target, str) and target not in flow.nodes:
                errors.append(f"{node_id}: {field} points to missing node {target!r}")
        timeout_target = node.get("timeout_target")
        if isinstance(timeout_target, str) and timeout_target not in flow.nodes:
            errors.append(f"{node_id}: timeout_target points to missing node {timeout_target!r}")
        if "timeout_target" in node and not isinstance(node.get("timeout_seconds"), int):
            errors.append(f"{node_id}: timeout_target requires integer timeout_seconds")

        media = node.get("media", [])
        if media is not None and not isinstance(media, list):
            errors.append(f"{node_id}: media must be a list")
        for index, item in enumerate(media or []):
            if not isinstance(item, dict):
                errors.append(f"{node_id}: media #{index + 1} must be a mapping")
                continue
            if item.get("type") not in {"photo", "video", "document"}:
                errors.append(f"{node_id}: media #{index + 1} has unsupported type")
            if not isinstance(item.get("path"), str):
                errors.append(f"{node_id}: media #{index + 1} must contain path")

    return errors
