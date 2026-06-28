from pathlib import Path


def test_images_data_references_existing_files() -> None:
    text = Path("images/data.txt").read_text(encoding="utf-8")
    for index in range(1, 7):
        assert f"images/k{index}.jpg" in text
        assert Path(f"images/k{index}.jpg").exists()


def test_videos_data_references_existing_files() -> None:
    text = Path("videos/data.txt").read_text(encoding="utf-8")
    assert "videos/dykhalka.mp4" in text
    assert Path("videos/dykhalka.mp4").exists()

