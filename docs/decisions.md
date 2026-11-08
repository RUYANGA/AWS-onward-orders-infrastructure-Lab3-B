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

Approximate US East list prices (eu-west-1 is slightly higher; confirm in the AWS Pricing
Calculator). Regional NAT Gateway: $0.045 per hour for each zone it serves plus $0.045 per GB
([Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/)). Free Tier credits not counted.

A quiet day runs 2 servers for 24 h. A peak day runs 6 servers for the 8-hour event and 2 for
the other 16 h, which is 80 server-hours.

| Item | Quiet day (USD) | Peak day (USD) |
| --- | --- | --- |
| Regional NAT Gateway, 2 zones | 2.16 | 2.16 |
| NAT public IPv4, 1 per zone | 0.24 | 0.24 |
| NAT data, 2 GB vs 5 GB | 0.09 | 0.23 |
| Application Load Balancer + LCUs | 0.73 | 1.00 |
| ALB public IPv4, 2 zones | 0.24 | 0.24 |
| EC2 t3.micro, 48 vs 80 server-hours | 0.50 | 0.83 |
| EBS gp3 8 GB per server | 0.04 | 0.06 |
| Detailed monitoring | 0.14 | 0.23 |
| **Total** | **≈ 4.14** | **≈ 4.99** |

That is roughly $125 for a quiet month.

The NAT gateway and load balancer are a fixed floor. Peak capacity costs well under $1 a day
because it exists only for the hours it is needed. Keeping 6 servers all month instead would
cost about $45 in compute against about $15 for the baseline of 2.

Delete the stack after demos (`scripts/teardown.sh`) and rebuild from Git when needed.
