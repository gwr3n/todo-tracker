#!/bin/bash
# Test the dump --history scenario in a temporary directory

# Use the todo CLI from the project
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TODO_CLI="$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/src/cli.py"

# Create temp test directory
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"

echo "=== Test Directory: $TEST_DIR ==="
echo

echo "=== Creating Task A (pending) ==="
$TODO_CLI add "Task A"

echo -e "\n=== Listing tasks ==="
$TODO_CLI list

echo -e "\n=== Getting Task A ID ==="
TASK_A_ID=$($TODO_CLI list | grep "Task A" | awk '{print $1}')
echo "Task A ID: $TASK_A_ID"

echo -e "\n=== Updating Task A to completed ==="
$TODO_CLI update "$TASK_A_ID" --status completed

echo -e "\n=== Creating Task B (pending) ==="
$TODO_CLI add "Task B"

echo -e "\n=== Listing all tasks ==="
$TODO_CLI list

echo -e "\n=== Dumping with --history ==="
DUMP_FILE="$TEST_DIR/dump.json"
$TODO_CLI dump --history > "$DUMP_FILE"

echo -e "\n=== Analyzing dump ==="
cat "$DUMP_FILE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total tasks in dump: {len(data)}')
print()
for i, task in enumerate(data, 1):
    print(f'{i}. {task[\"description\"]} - Status: {task[\"status\"]} - ID: {task[\"id\"][:8]}')
"

echo -e "\n=== Cleanup ==="
rm -rf "$TEST_DIR"
