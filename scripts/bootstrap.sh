#!/usr/bin/env bash
# Build (or rebuild) everything from this repository.
#   ./scripts/bootstrap.sh connection   # GitHub connection + Git sync role
#     -> authorise the connection once in the console (AWS requires a person to approve GitHub access)
#   ./scripts/bootstrap.sh sync         # Git sync creates onward-dev-orders from deployments/dev/orders.yaml
source "$(dirname "$0")/lib.sh"
phase="${1:?usage: bootstrap.sh connection|sync}"
case "$phase" in connection) ready=false ;; sync) ready=true ;; *) echo "unknown phase"; exit 1 ;; esac

say "Deploying onward-$ENVIRONMENT-bootstrap ($phase)"
aws cloudformation deploy --stack-name "onward-$ENVIRONMENT-bootstrap" \
  --template-file "$ROOT/bootstrap/bootstrap.yaml" --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset --tags Project=onward "Owner=$OWNER" "Environment=$ENVIRONMENT" \
  --parameter-overrides "Environment=$ENVIRONMENT" "Owner=$OWNER" "GitHubOwner=$GITHUB_OWNER" \
    "RepoName=$REPO_NAME" "ConnectionReady=$ready"

if [[ $phase == connection ]]; then
  say "Authorise the connection: Console > Developer Tools > Settings > Connections > onward-$ENVIRONMENT-github > Update pending connection"
  echo "Then run: ./scripts/bootstrap.sh sync"; exit 0
fi

say "Waiting for Git sync to create $STACK (about 8-12 minutes: NAT gateway, load balancer, 2 servers booting)"
for _ in $(seq 1 80); do
  s=$(aws cloudformation describe-stacks --stack-name "$STACK" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo WAITING)
  echo "$(date +%T) $s"
  case "$s" in CREATE_COMPLETE|UPDATE_COMPLETE) break ;; *FAILED|ROLLBACK_COMPLETE) echo "See the stack events"; exit 1 ;; esac
  sleep 20
done
say "Order system: $(out AppUrl)"
echo "Dashboard: $(out DashboardUrl)"
