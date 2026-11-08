#!/usr/bin/env bash
# Delete the environment after a demo; rebuild later with scripts/bootstrap.sh sync.
source "$(dirname "$0")/lib.sh"
read -r -p "Delete $STACK in $AWS_REGION? Type the environment name to confirm: " ok
[[ "$ok" == "$ENVIRONMENT" ]] || { echo "Cancelled."; exit 1; }
say "Stopping Git sync first so it does not recreate the stack"
aws cloudformation deploy --stack-name "onward-$ENVIRONMENT-bootstrap" --template-file "$ROOT/bootstrap/bootstrap.yaml" \
  --capabilities CAPABILITY_NAMED_IAM --no-fail-on-empty-changeset --parameter-overrides ConnectionReady=false
say "Deleting $STACK"
aws cloudformation delete-stack --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --stack-name "$STACK"
echo "Deleted. The bootstrap stack (connection + role) remains and costs nothing."
