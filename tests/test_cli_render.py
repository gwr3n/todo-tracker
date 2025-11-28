from src.cli import render_kanban_board
from src.models import Task
from uuid import UUID

def test_render_kanban_board():
    # Setup mock tasks
    t1 = Task(id=UUID('3077bee6-3da3-4783-aff7-cbedfd5f5592'), description="Task 1", status="pending")
    t2 = Task(id=UUID('c4709ac5-4034-f7bb-27ac-93b3596223f9'), description="Task 2", status="completed")
    
    tasks_by_status = {
        "pending": [t1],
        "completed": [t2]
    }
    
    statuses = ["pending", "completed"]
    
    # Render
    board = render_kanban_board(tasks_by_status, statuses)
    
    # Verify structure
    assert "PENDING" in board
    assert "COMPLETED" in board
    assert "Task 1" in board
    assert "Task 2" in board
    
    # Verify box drawing chars
    assert "┌" in board
    assert "┐" in board
    assert "└" in board
    assert "┘" in board

def test_render_kanban_empty_column():
    t1 = Task(id=UUID('3077bee6-3da3-4783-aff7-cbedfd5f5592'), description="Task 1", status="pending")
    
    tasks_by_status = {
        "pending": [t1],
        "completed": []
    }
    
    statuses = ["pending", "completed"]
    board = render_kanban_board(tasks_by_status, statuses)
    
    assert "Task 1" in board
    # Should still show header for empty column
    assert "COMPLETED" in board
