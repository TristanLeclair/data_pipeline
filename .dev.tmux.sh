#! /usr/bin/env bash

directory_basename=${PWD##*/}

if ! tmux has-session -t "$directory_basename" 2>/dev/null;
then
  tmux new-session -s "$directory_basename" -n Code -d

  tmux new-window -t "$directory_basename":2 -n Kafka
  tmux new-window -t "$directory_basename":3 -n Tests
  tmux new-window -t "$directory_basename":4 -n Zsh

  tmux split-pane -t "$directory_basename":1 -v -l '20%'
  tmux split-pane -t "$directory_basename":3 -v

  sleep 2


  tmux send-keys -t "$directory_basename":1.1 "stenv" C-m
  tmux send-keys -t "$directory_basename":1.2 "stenv" C-m
  tmux send-keys -t "$directory_basename":2 "stenv" C-m
  tmux send-keys -t "$directory_basename":3.1 "stenv" C-m
  tmux send-keys -t "$directory_basename":3.2 "stenv" C-m
  tmux send-keys -t "$directory_basename":4 "stenv" C-m

  sleep 1

  tmux send-keys -t "$directory_basename":2 "docker compose up" C-m
  tmux send-keys -t "$directory_basename":3.1 "make start-producer"
  tmux send-keys -t "$directory_basename":3.2 "make start-consumer"

  tmux select-window -t "$directory_basename":1
fi

if [ "$TERM_PROGRAM" = tmux ]; then
  tmux switchc -t "$directory_basename"
else
  tmux attach -t "$directory_basename"
fi
