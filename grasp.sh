#!/bin/bash

CMD=$1

if [ "$CMD" = "dev" ]; then
  trap "exit" INT TERM ERR
  trap "kill 0" EXIT
  echo "Starting DEV python server"
  python3 main.py --debug --port 8003 --db_auth=/home/jrumsevi/auth.txt &
  python_pid=$!
  echo "Starting DEV node server"
  cd frontend/
  npm run watch &
  npm_pid=$!
  cd ..
  echo "python pid $python_pid"
  echo "npm pid $npm_pid"
  wait
fi

if [ "$CMD" = "build" ]; then
  echo "Building for production"
  cd vue_frontend/
  npm run build
  cd ..
fi

if [ "$CMD" = "start" ]; then
  echo "Starting GrASP"
  nohup python3 $(pwd)/main.py --port 8003 &
  echo "Started with pid $!"
fi
