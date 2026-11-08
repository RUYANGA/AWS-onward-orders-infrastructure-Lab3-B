#!/usr/bin/env bash
# No inline IAM policies, no IAM users or keys, no SSH key pairs, no AWS keys in the repo.
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
grep -nE 'Type:\s*"?AWS::IAM::(Policy|UserPolicy|GroupPolicy|RolePolicy|User|AccessKey)"?\s*$' templates/*.yaml bootstrap/*.yaml && { echo "FAIL: inline policy / user / key resource"; fail=1; }
grep -nE '^\s+Policies:' templates/*.yaml bootstrap/*.yaml && { echo "FAIL: inline Policies block"; fail=1; }
grep -nE '^\s+KeyName:|AWS::EC2::KeyPair|FromPort: 22\b' templates/*.yaml && { echo "FAIL: SSH key or port 22"; fail=1; }
git grep -nIE '(AKIA|ASIA)[0-9A-Z]{16}|aws_secret_access_key' -- . ':!scripts/check_standards.sh' 2>/dev/null && { echo "FAIL: AWS key committed"; fail=1; }
[[ $fail == 0 ]] && echo "PASS: managed policies only; no IAM users, access keys, SSH keys or port 22"
exit $fail
