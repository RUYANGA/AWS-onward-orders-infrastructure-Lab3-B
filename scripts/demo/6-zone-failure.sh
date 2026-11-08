#!/usr/bin/env bash
# Client check: the application keeps working if one Availability Zone is lost.
#   ./6-zone-failure.sh            simulate losing zone "a": the group may only use zone b,
#                                   so zone-a servers are replaced in zone b
#   ./6-zone-failure.sh restore    give the group both zones back (matches the template)
# Keep 3-watch-servers.sh running: answers continue throughout, from zone b.
# (This briefly changes the group outside CloudFormation; "restore" undoes it.)
source "$(dirname "$0")/../lib.sh"
subnets=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG" --query 'AutoScalingGroups[0].VPCZoneIdentifier' --output text)
vpc=$(out VpcId)
a=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpc" "Name=tag:Name,Values=onward-$ENVIRONMENT-private-a" --query 'Subnets[0].SubnetId' --output text)
b=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpc" "Name=tag:Name,Values=onward-$ENVIRONMENT-private-b" --query 'Subnets[0].SubnetId' --output text)
if [[ "${1:-}" == restore ]]; then
  say "Restoring both zones"
  aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG" --vpc-zone-identifier "$a,$b"
else
  say "Zone a is 'lost': removing it from the group (was: $subnets)"
  aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG" --vpc-zone-identifier "$b"
fi
for _ in $(seq 1 18); do sleep 20; echo "--- $(date +%T)"; servers; done
