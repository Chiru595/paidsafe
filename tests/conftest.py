import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

OWNER = "@switch-test-owner:localhost"
ACCOUNTANT = "@switch-test-accountant:localhost"
IMPOSTOR = "@switch-test-impostor:localhost"
ROOM = "test-room"


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Each test gets its own state db, outbox, playbooks and roles file."""
    import tools.common as common
    import tools.memory as memory
    import tools.send_client_message as scm

    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "roles.json").write_text(json.dumps({"owner": OWNER, "accountant": ACCOUNTANT}))
    monkeypatch.setattr(common, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(common, "CONFIG", cfg)
    monkeypatch.setattr(scm, "OUTBOX", tmp_path / "outbox")
    monkeypatch.setattr(memory, "PLAYBOOKS", tmp_path / "playbooks")
    return tmp_path
