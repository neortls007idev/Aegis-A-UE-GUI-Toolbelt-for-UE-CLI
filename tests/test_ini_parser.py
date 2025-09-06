from pathlib import Path

from aegis.core.ini_parser import get_value, parse_ini


def test_parse_ini_operators(tmp_path: Path) -> None:
    cfg = tmp_path / "Default.ini"
    cfg.write_text(
        """
[Sec]
+Add=A
+Add=A
Base=1
.Base=2
-Base=1
!Remove
Remove=42
Flag
""",
        encoding="utf-8",
    )
    data = parse_ini(cfg)
    assert data["Sec"]["Add"] == ["A"]
    assert data["Sec"]["Base"] == ["2"]
    assert data["Sec"]["Remove"] == ["42"]
    assert data["Sec"]["Flag"] == [None]
    assert get_value(data, "Sec", "Base") == "2"
    assert get_value(data, "Sec", "Flag") is None
