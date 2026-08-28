from pathlib import Path


def test_public_layout():
    root = Path(__file__).resolve().parents[1]
    assert (root / "app" / "main.py").exists()
    assert (root / "web" / "package.json").exists()
    assert (root / ".env.example").exists()

