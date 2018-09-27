#!/bin/bash
until python3.5 main.py; do
    echo "'mox' crashed with exit code $?. Restarting in 45s..." >&2
    sleep 45
done
