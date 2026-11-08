#!/usr/bin/env bash
# Client check: a failed server is replaced without manual action.
#   ./5-server-failure.sh          terminate one server (hardware/instance failure)
#   ./5-server-failure.sh app      stop the app on one server (it stays running but
#                                   fails the load balancer health check; ELB health
#                                   checks make Auto Scaling replace it)
# Keep 3-watch-servers.sh running: answers continue from the other server.
source "$(dirname "$0")/../lib.sh"
victim=$(servers | awk '$3=="InService"{print $1; exit}')
if [[ "${1:-}" == app ]]; then
  say "Stopping the app on $victim through Systems Manager"
  aws ssm send-command --document-name AWS-RunShellScript --instance-ids "$victim" \
    --parameters 'commands=["systemctl stop onward-orders"]' --comment "Simulated app failure" >/dev/null
else
  say "Terminating $victim"
  aws ec2 terminate-instances --instance-ids "$victim" --query 'TerminatingInstances[0].CurrentState.Name' --output text
fi
for _ in $(seq 1 20); do sleep 20; echo "--- $(date +%T)"; servers; done
