
#!/usr/bin/env bash

printf '\e[?25l'           # hide cursor
trap 'printf "\e[?25h"' EXIT

# Do a full clear only once
printf '\e[2J\e[H'

while true; do
    # Go home, clear only below current cursor to end of screen
    printf '\e[H'
    todo kanban pending in-progress completed
    printf '\e[J'
    sleep 1
done
