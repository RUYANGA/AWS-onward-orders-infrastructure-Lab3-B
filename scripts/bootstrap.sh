#!/usr/bin/env bash
# Build (or rebuild) everything from this repository.
#   ./scripts/bootstrap.sh connection   # GitHub connection + Git sync role
#     -> authorise the connection once in the console (AWS requires a person to approve GitHub access)
#   ./scripts/bootstrap.sh sync         # Git sync creates onward-dev-orders from deployments/dev/orders.yaml
# With an existing GitHub connection, skip the first step and the console:
#   CONNECTION_ARN=<arn of an AVAILABLE connection> ./scripts/bootstrap.sh sync
source "$(dirname "$0")/lib.sh"
phase="${1:?usage: bootstrap.sh connection|sync}"
case "$phase" in connection) ready=false ;; sync) ready=true ;; *) echo "unknown phase"; exit 1 ;; esac
if [[ -n "$CONNECTION_ARN" ]]; then
  status=$(aws codeconnections get-connection --connection-arn "$CONNECTION_ARN" \
    --query Connection.ConnectionStatus --output text)
  [[ "$status" == AVAILABLE ]] || { echo "Connection $CONNECTION_ARN is $status, not AVAILABLE"; exit 1; }
  say "Reusing the existing GitHub connection (AVAILABLE): $CONNECTION_ARN"
  ready=true
fi

# Git sync only updates stacks that already exist: create an empty placeholder first.
if [[ $ready == true ]] && ! aws cloudformation describe-stacks --stack-name "$STACK" >/dev/null 2>&1; then
  say "Creating the empty placeholder stack $STACK (Git sync only updates existing stacks)"
  aws cloudformation deploy --stack-name "$STACK" --template-file "$ROOT/templates/gitsync-placeholder.yaml" \
    --no-fail-on-empty-changeset --tags Project=onward "Owner=$OWNER" "Environment=$ENVIRONMENT"
fi

# The Regional NAT Gateway needs AWSServiceRoleForNATGateway; the bootstrap creates it unless it exists.
create_nat_slr=true
aws iam get-role --role-name AWSServiceRoleForNATGateway >/dev/null 2>&1 && create_nat_slr=false

# GitHub owner names are case-insensitive, but the repository link only accepts lowercase.
say "Deploying onward-$ENVIRONMENT-bootstrap ($phase)"
aws cloudformation deploy --stack-name "onward-$ENVIRONMENT-bootstrap" \
  --template-file "$ROOT/bootstrap/bootstrap.yaml" --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset --tags Project=onward "Owner=$OWNER" "Environment=$ENVIRONMENT" \
  --parameter-overrides "Environment=$ENVIRONMENT" "Owner=$OWNER" "GitHubOwner=${GITHUB_OWNER,,}" \
    "RepoName=$REPO_NAME" "ConnectionReady=$ready" "ExistingConnectionArn=$CONNECTION_ARN" \
    "CreateNatGatewayServiceLinkedRole=$create_nat_slr"

if [[ $phase == connection && -z "$CONNECTION_ARN" ]]; then
  say "Authorise the connection: Console > Developer Tools > Settings > Connections > onward-$ENVIRONMENT-github > Update pending connection"
  echo "Then run: ./scripts/bootstrap.sh sync"; exit 0
fi

say "Waiting for Git sync to build $STACK (about 8-12 minutes: NAT gateway, load balancer, 2 servers booting)"
for _ in $(seq 1 80); do
  s=$(aws cloudformation describe-stacks --stack-name "$STACK" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo WAITING)
  echo "$(date +%T) $s"
  # The placeholder is CREATE_COMPLETE; Git sync's real template arrives as an update.
  case "$s" in UPDATE_COMPLETE) break ;; *ROLLBACK*|*FAILED) echo "See the stack events"; exit 1 ;; esac
  sleep 20
done
say "Order system: $(out AppUrl)"
echo "Dashboard: $(out DashboardUrl)"
