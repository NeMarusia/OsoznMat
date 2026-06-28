from pathlib import Path
from urllib.parse import urlparse

import yaml


def test_link_candidates_include_all_flow_urls() -> None:
    flow = yaml.safe_load(Path("data/flow.yaml").read_text(encoding="utf-8"))
    candidates = Path("data/link_candidates.md").read_text(encoding="utf-8")
    urls = set()
    for node in flow["nodes"].values():
        for button in node.get("buttons", []) or []:
            if button.get("url"):
                urls.add(button["url"])
        text = node.get("text") or ""
        for part in text.split():
            if part.startswith("http"):
                urls.add(part.strip("().,"))

    assert urls
    for url in urls:
        assert url in candidates
        assert urlparse(url).scheme in {"http", "https"}

