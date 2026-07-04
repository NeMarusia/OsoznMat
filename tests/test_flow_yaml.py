from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

from bot.flow_loader import load_flow, override_timing_seconds, validate_flow
from bot.main import completed_node_ids


FLOW_PATH = Path("data/flow.yaml")


def test_flow_yaml_is_valid() -> None:
    flow = load_flow(FLOW_PATH)
    assert flow.start == "kk1"
    assert validate_flow(flow) == []


def test_flow_contains_required_nodes() -> None:
    flow = load_flow(FLOW_PATH)
    required = {
        "kk1",
        "kk6",
        "kk10",
        "kk11",
        "kk14",
        "kk17",
        "kk18",
        "kk19",
        "kk20",
        "kk24",
        "kk25",
        "kk26",
        "kk27",
        "kk28",
        "kk29",
        "kk30",
        "kk31",
        "kk32",
        "kk33",
        "kk34",
        "kk35",
        "kk36",
    }
    assert required <= set(flow.nodes)


def test_kk20_routes_to_correct_and_incorrect_nodes() -> None:
    flow = load_flow(FLOW_PATH)
    kk20 = flow.get("kk20")
    assert kk20["input_handler"] == "kk20_answer"
    assert kk20["correct"] == "kk25"
    assert kk20["incorrect"] == "kk26"


def test_ignore_timeouts_are_configured() -> None:
    flow = load_flow(FLOW_PATH)
    assert flow.get("kk1")["timeout_seconds"] == 86400
    assert flow.get("kk1")["timeout_target"] == "kk6"
    assert flow.get("kk6")["timeout_seconds"] == 86400
    assert flow.get("kk6")["timeout_target"] == "kk20"
    assert flow.get("kk20")["timeout_seconds"] == 86400
    assert flow.get("kk20")["timeout_target"] == "kk28"
    assert flow.get("kk17")["delay_seconds"] == 86400
    assert flow.get("kk18")["delay_seconds"] == 86400
    assert flow.get("kk27")["delay_seconds"] == 86400
    assert flow.get("kk29")["delay_seconds"] == 86400


def test_override_timing_seconds_updates_only_timing_nodes() -> None:
    flow = load_flow(FLOW_PATH)
    debug_flow = override_timing_seconds(flow, 30)

    assert debug_flow.get("kk1")["timeout_seconds"] == 30
    assert debug_flow.get("kk6")["timeout_seconds"] == 30
    assert debug_flow.get("kk20")["timeout_seconds"] == 30
    assert debug_flow.get("kk17")["delay_seconds"] == 30
    assert debug_flow.get("kk18")["delay_seconds"] == 30
    assert debug_flow.get("kk27")["delay_seconds"] == 30
    assert debug_flow.get("kk29")["delay_seconds"] == 30
    assert "timeout_seconds" not in debug_flow.get("kk10")
    assert "delay_seconds" not in debug_flow.get("kk10")
    assert flow.get("kk1")["timeout_seconds"] == 86400
    assert flow.get("kk17")["delay_seconds"] == 86400


def test_urls_keep_tracking_parameters() -> None:
    flow = load_flow(FLOW_PATH)
    urls = collect_urls(flow)
    assert urls
    for url in urls:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        assert parsed.scheme in {"http", "https"}
        assert parsed.netloc
        assert query.get("utm_source") == ["bot"]
        assert query.get("utm_medium") == ["voronka1"]
        assert query.get("utm_campaign") == ["kurs"]
        assert "utm_content" in query


def test_markdown_links_are_in_text() -> None:
    flow = load_flow(FLOW_PATH)
    markdown_nodes = {"kk6", "kk25", "kk26", "kk28", "kk31", "kk33", "kk34", "kk35"}
    for node_id in markdown_nodes:
        node = flow.get(node_id)
        assert node["parse_mode"] == "Markdown"
        assert re.search(r"\[[^\]]+\]\(https://[^)]+\)", node["text"]), node_id

    assert "[курс](" in flow.get("kk25")["text"]
    assert "[курс](" in flow.get("kk6")["text"]
    assert "utm_content=day1" in flow.get("kk6")["text"]
    assert "[курсе](" in flow.get("kk26")["text"]
    assert "[курса](" in flow.get("kk28")["text"]
    assert "[сайте](" in flow.get("kk31")["text"]
    assert "[Познакомиться с услугами](" in flow.get("kk33")["text"]
    assert "[Перейти на сайт](" in flow.get("kk34")["text"]
    assert "[Записаться на курс](" in flow.get("kk35")["text"]


def test_media_paths_exist() -> None:
    flow = load_flow(FLOW_PATH)
    media_paths = [
        Path(item["path"])
        for node in flow.nodes.values()
        for item in node.get("media", [])
    ]
    assert media_paths
    for path in media_paths:
        assert path.exists(), path


def test_kk1_sends_guide_pdf_as_document() -> None:
    flow = load_flow(FLOW_PATH)
    kk1_media = flow.get("kk1")["media"]
    assert kk1_media == [{"type": "document", "path": "files/guide.pdf"}]
    assert Path("files/guide.pdf").exists()


def test_completed_node_ids_are_terminal_flow_nodes() -> None:
    flow = load_flow(FLOW_PATH)

    assert completed_node_ids(flow) == {"kk31", "kk33", "kk34", "kk35", "kk36"}


def collect_urls(flow) -> list[str]:
    urls: list[str] = []
    for node in flow.nodes.values():
        for button in node.get("buttons", []) or []:
            if button.get("url"):
                urls.append(button["url"])
        urls.extend(re.findall(r"https://[^)\s]+", node.get("text") or ""))
    return urls
