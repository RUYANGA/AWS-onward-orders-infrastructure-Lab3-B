# Shared helpers, sourced by the other scripts.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Defaults for this project. Override any of them for one run, e.g. ENVIRONMENT=test ./scripts/bootstrap.sh sync
# (deployments/dev/orders.yaml holds the same Environment and Owner values for Git sync).
AWS_REGION="${AWS_REGION:-eu-west-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
OWNER="${OWNER:-Merci RUYANGA}"
GITHUB_OWNER="${GITHUB_OWNER:-RUYANGA}"
REPO_NAME="${REPO_NAME:-AWS-Onward-Order-EC2-Lab3-B}"
export AWS_REGION AWS_DEFAULT_REGION="$AWS_REGION"
STACK="onward-${ENVIRONMENT}-orders"
ASG="onward-${ENVIRONMENT}-orders"

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
out() { aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
servers() {  # instance  AZ  lifecycle  health
  aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG" \
    --query 'AutoScalingGroups[0].Instances[].[InstanceId,AvailabilityZone,LifecycleState,HealthStatus]' --output text
}
capacity() {
  aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG" \
    --query 'AutoScalingGroups[0].{min:MinSize,desired:DesiredCapacity,max:MaxSize,inService:length(Instances[?LifecycleState==`InService`])}' --output text
}
# run_on_servers "<shell command>"  -> runs through Systems Manager, prints each server's output
run_on_servers() {
  local id
  id=$(aws ssm send-command --document-name AWS-RunShellScript \
        --targets "Key=tag:aws:autoscaling:groupName,Values=$ASG" \
        --parameters "commands=[\"$1\"]" --comment "onward live review" \
        --query Command.CommandId --output text)
  sleep 8
  aws ssm list-command-invocations --command-id "$id" --details \
    --query 'CommandInvocations[].[InstanceId,Status,CommandPlugins[0].Output]' --output text
}
