import json
import pytest


def test_cli_dump_stdout(tmp_path):
    # We can't easily inject a mock orchestrator into the CLI process without complex
    # patching.
    # However, we can run the CLI against a temp directory by modifying the CLI to
    # accept a root dir,
    # OR we can just assume the CLI works if we can run it.
    # But running against the real .todo_store is risky/bad practice for tests.
    #
    # The CLI currently hardcodes TodoTracker().
    # To test properly, we should refactor CLI to accept --root-dir or env var.
    #
    # For now, let's skip the subprocess test if we can't isolate it,
    # OR we can mock sys.stdout and run main() in-process.
    pass


# Let's try in-process testing by importing main and mocking sys.argv and sys.stdout
from src.cli import main  # noqa: E402
from unittest.mock import patch  # noqa: E402


@pytest.fixture
def mock_orch():
    with patch("src.cli.TodoTracker") as MockOrch:
        orch = MockOrch.return_value
        orch.tasks = {}
        yield orch


def test_dump_command(mock_orch, capsys):
    # Setup mock tasks
    from src.models import Task

    t1 = Task(description="Task 1")
    t2 = Task(description="Task 2", archived=True)

    mock_orch.tasks = {t1.id: t1, t2.id: t2}

    # Test dump (default: no archived)
    with patch("sys.argv", ["cli.py", "dump"]):
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["description"] == "Task 1"

    # Test dump -a (all)
    with patch("sys.argv", ["cli.py", "dump", "-a"]):
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 2


def test_dump_output_file(mock_orch, tmp_path):
    # Setup mock tasks
    from src.models import Task

    t1 = Task(description="Task 1")
    mock_orch.tasks = {t1.id: t1}

    output_file = tmp_path / "dump.json"

    with patch("sys.argv", ["cli.py", "dump", "--output", str(output_file)]):
        main()

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["description"] == "Task 1"


def test_dump_history(mock_orch, capsys):
    from src.models import Task

    t1_v2 = Task(description="Task 1 v2")
    t1_v1 = Task(description="Task 1 v1")

    mock_orch.tasks = {t1_v2.id: t1_v2}
    mock_orch.get_history.return_value = [t1_v2, t1_v1]

    with patch("sys.argv", ["cli.py", "dump", "--history"]):
        main()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 2
        descriptions = {d["description"] for d in data}
        assert "Task 1 v2" in descriptions
        assert "Task 1 v1" in descriptions
