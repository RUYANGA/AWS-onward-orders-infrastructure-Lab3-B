#!/usr/bin/env bash
# Client check: rising demand grows the number of servers, and it shrinks afterwards.
# Triggers a time-limited CPU spike through Systems Manager Run Command (IAM-controlled,
# logged, no ports, nothing exposed on the website), then watches capacity.
# Expect: scale-out within ~3-5 minutes; scale-in ~15 minutes after the spike ends.
source "$(dirname "$0")/../lib.sh"
minutes="${1:-10}"
say "Starting a $minutes-minute CPU spike on every server in $ASG"
aws ssm send-command --document-name "$(out CpuSpikeDocumentName)" \
  --targets "Key=tag:aws:autoscaling:groupName,Values=$ASG" \
  --parameters "Minutes=$minutes" --comment "Sales-day load demo" \
  --query 'Command.{Id: CommandId, Status: Status}' --output table
say "Watching capacity (Ctrl-C to stop). Dashboard: $(out DashboardUrl)"
while true; do
  printf '%s  min/desired/max/in-service: %s\n' "$(date +%T)" "$(capacity | tr '\t' ' ')"
  sleep 30
done
