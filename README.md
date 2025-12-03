# Todo Tracker

A powerful git-styled CLI-based todo task tracker with versioning, attachments, and Kanban visualization.

Core package badges:

![Codecov (with branch)](https://img.shields.io/codecov/c/gh/gwr3n/todo-tracker/main)
 ![Python package](https://img.shields.io/github/actions/workflow/status/gwr3n/todo-tracker/.github%2Fworkflows%2Fpython-package.yml) ![Lint and type-check](https://img.shields.io/github/actions/workflow/status/gwr3n/todo-tracker/.github%2Fworkflows%2Flint-type.yml?branch=main&label=lint%20%2B%20type-check) [![PyPI](https://img.shields.io/pypi/v/todo-tracker)](https://pypi.org/project/todo-tracker/) [![Python versions](https://img.shields.io/pypi/pyversions/todo-tracker)](https://pypi.org/project/todo-tracker/) [![License](https://img.shields.io/github/license/gwr3n/todo-tracker)](LICENSE) [![Downloads](https://static.pepy.tech/badge/todo-tracker)](https://pepy.tech/project/todo-tracker) [![Release](https://img.shields.io/github/v/release/gwr3n/todo-tracker)](https://github.com/gwr3n/todo-tracker/releases) [![Wheel](https://img.shields.io/pypi/wheel/todo-tracker)](https://pypi.org/project/todo-tracker/)

Quality and tooling:

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000?logo=python)](https://github.com/psf/black) [![Ruff](https://img.shields.io/badge/lint-ruff-1f79ff?logo=python)](https://github.com/astral-sh/ruff) [![mypy](https://img.shields.io/badge/type--checked-mypy-blue?logo=python)](https://github.com/python/mypy)

Project/community:

[![Issues](https://img.shields.io/github/issues/gwr3n/todo-tracker)](https://github.com/gwr3n/todo-tracker/issues) [![PRs](https://img.shields.io/github/issues-pr/gwr3n/todo-tracker)](https://github.com/gwr3n/todo-tracker/pulls) [![Stars](https://img.shields.io/github/stars/gwr3n/todo-tracker?style=social)](https://github.com/gwr3n/todo-tracker/stargazers)

Docs:

[![Docs](https://img.shields.io/badge/docs-site-blue)](https://github.com/gwr3n/todo-tracker)

## Features

*   **Task Management**: Create, update, and manage tasks with descriptions, deadlines, and statuses.
*   **Versioning**: Every change to a task is versioned. You can view the full history of a task and revert to previous states (conceptually).
*   **Attachments**: Attach files to tasks. Files are stored efficiently using content-addressable storage (deduplication).
*   **Aliases**: Tasks are assigned human-readable aliases (e.g., `Misty-Rat`) for easier reference than UUIDs.
*   **Kanban Board**: Visualize your tasks in a terminal-based Kanban board. 
*   **Archiving**: Archive completed or stale tasks to keep your active list clean.
*   **JSON Dump**: Export your data to [JSON](json/counter_tasks.json) for backup or analysis.
<br>
<br>
<div style="text-align: center;">
    <img src="img/kanban.png" alt="Kanban" width="50%">
</div>
<br>
<br>
<div style="text-align: center;">
    <img src="img/CLI.png" alt="CLI" width="85%">
</div>

## Installation

Ensure you have Python 3.8+ installed.

1.  Clone the repository:
    ```bash
    git clone https://github.com/gwr3n/todo-tracker.git
    cd todo-tracker
    ```

2.  Install the package:
    ```bash
    pip install todo-tracker
    ```

## Usage

The main command is `todo`.

### Basic Operations

*   **Add a task:**
    ```bash
    todo add "Buy groceries" --deadline 2023-12-31
    ```

*   **List tasks:**
    ```bash
    todo list
    todo list --all  # Include archived tasks
    ```

*   **Show task details:**
    ```bash
    todo show <task_id_or_alias>
    ```

*   **Update a task:**
    ```bash
    todo update <id> --status "in-progress" --desc "Buy organic groceries"
    ```

### Attachments

*   **Attach a file:**
    ```bash
    todo attach <id> ./path/to/file.txt
    ```

*   **Extract an attachment:**
    ```bash
    todo extract <id> file.txt --output ./downloaded_file.txt
    ```

### Organization & Visualization

*   **Kanban View:**
    ```bash
    todo kanban pending in-progress done
    ```

*   **Archive/Unarchive:**
    ```bash
    todo archive <id>
    todo unarchive <id>
    ```

*   **Delete:**
    ```bash
    todo delete <id>
    ```

### Advanced

*   **View History:**
    ```bash
    todo history <id>
    ```

*   **Duplicate Task:**
    ```bash
    todo duplicate <id>
    ```

*   **Dump Data:**
    ```bash
    todo dump --output backup.json
    todo dump --history --all --output full_backup.json
    ```

## Data Storage

Data is stored in a `.todo_store` directory in the current working directory. This directory contains:
*   `objects/`: Content-addressable storage for task versions and attachment blobs.
*   `refs/`: References to the current version of each task.
*   `orchestrator.lock`: Lock file to ensure data integrity during concurrent access.

## Development

To run tests:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

