from app.core.executor import build_ps_command, ps_literal


def _bind(client, action="obs.scene", executable="notepad.exe", args=""):
    """Configure an action binding through the admin form."""
    return client.post(
        "/admin/actions",
        data={"action": action, "executable": executable, "args": args},
        follow_redirects=False,
    )


def test_dispatch_configured_action(client):
    assert _bind(client).status_code == 303
    response = client.post("/actions", json={"action": "obs.scene", "label": "Cena"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["action"] == "obs.scene"
    assert body["executed_at"]


def test_dispatch_records_last_run_on_binding(client):
    _bind(client)
    client.post("/actions", json={"action": "obs.scene"})
    page = client.get("/admin/actions")
    assert "notepad.exe" in page.text


def test_dispatch_unknown_action_is_not_executed(client):
    response = client.post("/actions", json={"action": "nao.configurada"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unknown"
    assert body["executed_at"] is None


def test_dispatch_never_maps_arbitrary_strings(client):
    # Without a binding, even shell-looking action keys are inert.
    client.post("/admin/actions", data={"action": "luz.mesa", "executable": "x"})
    body = client.post("/actions", json={"action": "rm -rf /"}).json()
    assert body["status"] == "unknown"


def test_dispatch_requires_action(client):
    assert client.post("/actions", json={"label": "sem ação"}).status_code == 422


def test_ps_literal_escapes_single_quotes():
    assert ps_literal("it's") == "'it''s'"


def test_build_ps_command_quotes_paths_and_args():
    assert (
        build_ps_command("C:\\Program Files\\App\\app.exe", "-a b")
        == "Start-Process -FilePath 'C:\\Program Files\\App\\app.exe' -ArgumentList '-a b'"
    )
    assert build_ps_command("notepad.exe", "  ") == "Start-Process -FilePath 'notepad.exe'"