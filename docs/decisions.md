# Decision log

| # | Decision | Reason in business terms | Rejected alternative |
| --- | --- | --- | --- |
| 1 | Region eu-west-1 | Consistent with the rest of Onward's environment; every service needed; lower prices than af-south-1 | af-south-1 (opt-in, higher cost). Confirm data residency before production data |
| 2 | Auto Scaling group, minimum 2, maximum 6, two zones | One server per zone survives a zone loss; 6 covers three times normal demand while capping spend | Fixed peak-size fleet (about 3× the compute all month); a single server (no resilience) |
| 3 | Target tracking on 50% average CPU | One setting follows real demand; 50% leaves headroom while a new server boots (about 3 min) | Scheduled scaling only (misses surprise spikes); manual scaling (people mid-event) |
| 4 | Detailed (1-minute) monitoring | Scaling reacts in minutes instead of 5-minute steps; about $2 per server per month | Basic monitoring (slower reaction at the peak) |
| 5 | ELB health checks on the group | Replaces servers whose app is broken, not only those that crashed | EC2 status checks only |
| 6 | Regional NAT Gateway | One managed gateway that follows servers into every zone; no NAT subnet or per-zone routes | One zonal NAT (a zone outage cuts updates everywhere); NAT per zone (same cost, more to manage); NAT instance (a server to patch, single point of failure) |
| 7 | Servers install the app at boot from Git at a pinned version | Every server is identical and disposable; no manual setup; versions are traceable | Hand-built servers; a custom AMI (faster boot, but needs an image pipeline: a later step) |
| 8 | Rolling replacement on template changes, at least one server in service | App releases and launch template changes cause no downtime | Replacing all servers at once |
| 9 | No SSH, no key pairs; Session Manager | Meets "no admin ports"; IAM-controlled and logged | SSH with keys; a bastion host (another public server) |
| 10 | CPU spike through a Run Command document, 15-minute cap | Secure, logged, time-limited demo trigger | A public "stress" button (anyone could run up cost) |
| 11 | IMDSv2 required, hop limit 1 | Blocks a common credential-theft path | IMDSv1 |
| 12 | t3 unlimited credits | CPU metrics reflect real load, so scaling works; a few cents of surplus credits on peak days | Standard credits (servers throttle to baseline when credits run out and scaling misreads load) |
| 13 | HTTP for dev | No company domain yet; adding an ACM certificate and a 443 listener enables HTTPS | Self-signed certificates |
| 14 | Stateless order desk | Any server can answer any request, which makes scaling safe | A shared database is a later step |

## Cost

The full estimate, with live eu-west-1 prices, every line item and the inputs for the AWS
Pricing Calculator, is in [cost-estimate.md](cost-estimate.md).

| Month | Estimated cost (USD) |
| --- | --- |
| Quiet month: 2 servers all month | 128.96 |
| Busy month: 4 sales days, 6 servers for 8 hours each | 139.22 |

The Regional NAT Gateway (billed per Availability Zone), the load balancer hours and four public
IPv4 addresses are a fixed floor of USD 103.08 a month, 80% of a quiet month. Each sales day adds
only about USD 2.57, because the extra servers exist only while they are needed. Keeping 6 servers
all month would cost USD 49.93 in compute against USD 16.64 for the baseline of 2.

Delete the stack after demos (`scripts/teardown.sh`) and rebuild from Git when needed.
