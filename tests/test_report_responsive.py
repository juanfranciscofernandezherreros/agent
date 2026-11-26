from app.report_responsive import STYLE, make_folder_responsive


def test_responsive_style_has_dedicated_technical_sheet_layout():
    assert 'id="agent-responsive-layout-v3"' in STYLE
    assert ".shell>main" in STYLE
    assert ".sidebar" in STYLE
    assert "@media(max-width:900px)" in STYLE
    assert ".table-wrap>table" in STYLE
    assert "overflow-x:auto" in STYLE


def test_make_folder_responsive_injects_latest_layout_once(tmp_path):
    report = tmp_path / "analysis.html"
    report.write_text("<html><head></head><body><main>Ficha</main></body></html>", encoding="utf-8")

    assert make_folder_responsive(tmp_path) == 1
    generated = report.read_text(encoding="utf-8")
    assert 'id="agent-responsive-layout-v3"' in generated
    assert make_folder_responsive(tmp_path) == 0
    assert generated.count('id="agent-responsive-layout-v3"') == 1


def test_responsive_layout_uses_light_palette():
    assert "color-scheme:light!important" in STYLE
    assert "background:#fff!important" in STYLE
    assert "#243247" in STYLE
    assert "background:#f4f7fb!important" in STYLE
    assert "prefers-color-scheme:dark" in STYLE
