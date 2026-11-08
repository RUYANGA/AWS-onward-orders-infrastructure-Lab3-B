# onward-orders-ec2

The Onward Logistics order system, built to survive sales days: one CloudFormation
template (deployed from this repository by Git sync) and one full-stack Python
application (the UI and order logic served together by Flask).

```
customers ──► Application Load Balancer (public subnets, the ONLY public resource)
                 │  :8000, from the ALB's security group only
                 ▼
         Auto Scaling group, 2–6 × t3.micro Amazon Linux 2023 (private subnets, 2 AZs)
                 │  HTTPS out only
                 ▼
         Regional NAT Gateway ──► internet (updates, packages, GitHub, AWS APIs)
```

Diagrams: [docs/architecture.md](docs/architecture.md). Decisions and cost: [docs/decisions.md](docs/decisions.md).

## Repository layout

```
templates/orders.yaml        the whole environment: VPC, Regional NAT, ALB, launch template,
                             Auto Scaling group + CPU policy, Run Command document, dashboard
deployments/dev/orders.yaml  Git sync deployment file: parameters and tags for onward-dev-orders
bootstrap/bootstrap.yaml     turns Git sync on (GitHub connection, Git sync role, sync config)
app/                         the order application (Flask), its tests and gunicorn settings
scripts/cpu_spike.py         time-limited CPU burner, run on servers only via Run Command
scripts/bootstrap.sh         build or rebuild from scratch
scripts/teardown.sh          delete after a demo (cost control)
scripts/check_standards.sh   no inline policies, IAM users, keys, SSH or port 22 (also in CI)
scripts/demo/                one script per client check
```

## How a server gets the application

Nothing is installed by hand and there is no SSH. The launch template's user data runs
at first boot on every server:

1. `dnf upgrade --security` (outbound through the NAT gateway).
2. Installs `git`, Python 3.11 and the CloudFormation helper scripts.
3. Clones **this repository** at `AppVersion` (a branch, tag or commit SHA) into `/opt/onward/src`
   and installs `app/requirements.txt` into a virtualenv.
4. Writes `/etc/onward/app.env` (owner name, environment, version) and starts the
   `onward-orders` systemd service (gunicorn on :8000, runs as an unprivileged user,
   restarts on failure, read-only system directories).
5. Checks `/health` locally and signals CloudFormation that the server is ready.

The page shows the owner's name, the lab name, and the instance ID, Availability Zone and
private IP of the server that answered (read from IMDSv2). Responses are never cached,
so each refresh goes back through the load balancer.

**Releasing a new app version:** set `AppVersion` in `deployments/dev/orders.yaml` to the
new tag or commit SHA and commit. Git sync updates the launch template and CloudFormation
replaces servers one at a time, keeping at least one in service.

## Company standards

- **Naming:** `onward-dev-orders` (stack, ALB, target group, group, launch template, dashboard),
  `onward-dev-vpc`, `onward-dev-nat`, `onward-dev-alb`, and so on.
- **Tags:** the deployment file sets stack tags `Project=onward`, `Owner`, `Environment`, which
  CloudFormation copies to every taggable resource. Servers, volumes and network interfaces
  are tagged explicitly by the Auto Scaling group and launch template. Check:
  `aws resourcegroupstaggingapi get-resources --tag-filters Key=Project,Values=onward`.
- **No inline policies:** the server role uses the AWS managed `AmazonSSMManagedInstanceCore`;
  bootstrap permissions are `AWS::IAM::ManagedPolicy` resources. The Git sync role is
  explicitly denied `iam:PutRolePolicy`, `iam:CreateUser` and `iam:CreateAccessKey`.
- **Access:** no key pairs, no port 22, IMDSv2 required. Admins use Session Manager; every
  session and command is logged.

## Build or rebuild from scratch

Prerequisites: AWS CLI v2 signed in through SSO or a role; this repository pushed to GitHub
as a **public** repository (servers clone it without credentials). The region (`eu-west-1`),
environment (`dev`), owner and GitHub repository are defaults in `scripts/lib.sh`, so there is
nothing to configure; override one for a single run with e.g. `ENVIRONMENT=test`. If you
change the owner, change it in `deployments/dev/orders.yaml` too.

1. `./scripts/bootstrap.sh connection`, then authorise the GitHub connection once in the
   console. AWS requires a person to approve access to GitHub; it is the only console step.
2. `./scripts/bootstrap.sh sync`. Git sync creates `onward-dev-orders` in about 8–12 minutes
   and the script prints the public address and dashboard link.

From then on, every commit that changes `templates/orders.yaml` or `deployments/dev/orders.yaml`
updates the stack automatically.

## Demonstrating the client's checks

Open the dashboard (`DashboardUrl` output) and run `scripts/demo/3-watch-servers.sh` in a
second terminal throughout; it prints which server answered each request.

| Client check | How to show it |
| --- | --- |
| One public address that stays reachable as servers come and go | `AppUrl` output; `3-watch-servers.sh` keeps answering through every test below |
| Requests are shared and the page shows which server answered | Refresh the page, or watch the tally in `3-watch-servers.sh` |
| Servers grow with demand and shrink afterwards | `2-cpu-spike.sh 10` (Run Command, IAM-controlled, logged), or `4-load-test.py <AppUrl> 8 60` from your laptop. Scale-out takes about 3–5 minutes; scale-in about 15 minutes after the load stops |
| A failed server is replaced | `5-server-failure.sh` (terminate) or `5-server-failure.sh app` (unhealthy app) |
| Survives the loss of one Availability Zone | `6-zone-failure.sh`, then `6-zone-failure.sh restore` |
| Only the load balancer is public; servers can still download updates | `1-security-check.sh` |
| Cost and rejected alternatives | [docs/decisions.md](docs/decisions.md) |
| Rebuilt from the repository | `scripts/teardown.sh`, then the two bootstrap steps |

Demo tips: the CPU spike makes the 2 existing servers busy, so target tracking adds about
2 more to bring the average back to 50%. The load test spreads load over all servers and
can push the group further. t3 instances run in "unlimited" mode, so CPU is not throttled
during the demo; a 10-minute spike costs a few cents in surplus credits.

## Run the app locally

```bash
cd app
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt && python -m pytest -q
OWNER_NAME="Merci RUYANGA" flask --app wsgi run --port 8000
```
