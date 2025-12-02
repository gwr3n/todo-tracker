#!/bin/bash
while true; do
    tput cup 0 0   # Move cursor to row 0, column 0
    todo kanban pending in-progress completed
    sleep 1
done