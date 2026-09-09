import pytest

tkinter = pytest.importorskip("tkinter")


def test_app_builds_all_steps_without_exceptions(monkeypatch):
    """Istanzia la finestra in modalita' headless (Tk().withdraw()).

    Salta il test se non c'e' un display disponibile (es. CI senza Xvfb):
    non e' un errore del codice, solo un ambiente senza server X.
    """
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "test-token")

    import main

    try:
        app = main.App()
    except tkinter.TclError as exc:
        pytest.skip(f"Nessun display disponibile: {exc}")

    try:
        app.withdraw()
        app.update()

        assert app.decklist_text is not None
        assert str(app.resolve_button["state"]) == "normal"
        assert str(app.analyze_button["state"]) == "disabled"
        assert app.plan_tree is not None
    finally:
        app.destroy()
