from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bot.flow_loader import load_flow, validate_flow


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
    assert flow.get("kk1")["timeout_seconds"] == 60
    assert flow.get("kk1")["timeout_target"] == "kk6"
    assert flow.get("kk6")["timeout_seconds"] == 60
    assert flow.get("kk6")["timeout_target"] == "kk20"
    assert flow.get("kk20")["timeout_seconds"] == 60
    assert flow.get("kk20")["timeout_target"] == "kk28"


def test_urls_keep_tracking_parameters() -> None:
    flow = load_flow(FLOW_PATH)
    urls = [
        button["url"]
        for node in flow.nodes.values()
        for button in node.get("buttons", [])
        if button.get("url")
    ]
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
