#!/usr/bin/env bash
# Client check: requests are shared across servers; the app stays reachable as
# servers come and go. Prints which server answered each request and a running tally.
source "$(dirname "$0")/../lib.sh"
url="$(out AppUrl)"; declare -A tally; ok=0; bad=0
trap 'echo; for k in "${!tally[@]}"; do echo "$k ${tally[$k]}"; done; echo "ok=$ok failed=$bad"; exit' INT
while true; do
  body=$(curl -s -m 3 "$url/whoami") && code=200 || code=000
  server=$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d["instance"], d["az"])' "$body" 2>/dev/null || echo "no-answer")
  [[ $server == no-answer ]] && bad=$((bad+1)) || ok=$((ok+1))
  tally["$server"]=$(( ${tally["$server"]:-0} + 1 ))
  printf '%s  %s  %s\n' "$(date +%T)" "$code" "$server"
  sleep 0.5
done
