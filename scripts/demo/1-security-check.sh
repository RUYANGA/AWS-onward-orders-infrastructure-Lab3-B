#!/usr/bin/env bash
# Client check: only the load balancer is public; no one on the internet can reach
# a server directly; servers can still download updates.
source "$(dirname "$0")/../lib.sh"
vpc=$(out VpcId)

say "The one public address"
out AppUrl

say "Servers: private IPs only (PublicIp column must be None)"
aws ec2 describe-instances --filters "Name=tag:aws:autoscaling:groupName,Values=$ASG" "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].{Server: InstanceId, AZ: Placement.AvailabilityZone, PrivateIp: PrivateIpAddress, PublicIp: PublicIpAddress, KeyPair: KeyName}' --output table

say "Server firewall: inbound only from the load balancer on 8000, no port 22"
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$vpc" "Name=group-name,Values=onward-$ENVIRONMENT-orders-servers" \
  --query 'SecurityGroups[0].IpPermissions[].{Port: FromPort, From: UserIdGroupPairs[0].GroupId, Cidr: IpRanges[0].CidrIp}' --output table

say "Private route table: the only way out is the Regional NAT Gateway (outbound only)"
aws ec2 describe-route-tables --route-table-ids "$(out PrivateRouteTableId)" \
  --query 'RouteTables[0].Routes[].{Destination: DestinationCidrBlock, Via: NatGatewayId || GatewayId}' --output table
aws ec2 describe-nat-gateways --nat-gateway-ids "$(out NatGatewayId)" \
  --query 'NatGateways[0].{Mode: AvailabilityMode, State: State}' --output table

say "From inside each server (via Systems Manager, no SSH): updates are reachable"
run_on_servers "curl -sS -o /dev/null -w 'github.com HTTP %{http_code}\\n' https://github.com; dnf -q check-update --security >/dev/null; echo dnf security check exit=\$?"
