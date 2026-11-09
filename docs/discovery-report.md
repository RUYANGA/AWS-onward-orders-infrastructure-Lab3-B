# Discovery Report: Handling Sales Day Demand

| | |
|---|---|
| Lab | Handling Sales Day Demand |
| Name | Merci RUYANGA |
| Date | 9 November 2026 |
| Client | Onward Logistics (see the Client Profile) |

---

## 1. What you found

### The client's need

On sales days, when order volume triples within hours, Onward's merchants and customers must keep placing orders without delays or errors. Onward should pay for the extra capacity only while the rush lasts, and nobody should have to step in by hand.

### Solutions that exist

| Solution | How it works | Trade off for this client |
|---|---|---|
| One larger server (scale up) | Move the order system to a bigger server sized for the busiest hour. | Strength: simple, with nothing new to run. Weakness: one fault still stops all orders, and Onward pays peak-day prices every quiet day. |
| A fixed fleet behind a load balancer, resized by hand or on a schedule | Several servers share traffic. Engineers add servers before a planned sale and remove them afterwards. | Strength: survives a single server failure, and costs are predictable. Weakness: it misses surprise spikes, needs people awake and watching mid-event, and a forgotten scale-down means paying for idle servers. |
| An Auto Scaling group behind a load balancer, scaling on demand (chosen) | Identical servers in two Availability Zones sit behind one public load balancer. A target tracking policy adds servers when average CPU passes 50% and removes them when the rush ends. Unhealthy servers are replaced automatically. | Strength: follows real demand with no one involved, survives a server or zone failure, and extra servers cost money only for the hours they run. Weakness: a new server takes about 3 to 5 minutes to join, and the load balancer and NAT gateway are a fixed daily cost even when idle. |

### What happens with no solution

If the order system stays sized for a normal day, the first big sales day overloads it. Pages slow down, then fail, and merchants lose sales at the very moment they expected the most orders. Some of them will move to a competitor, because reliability is what Onward sells. Engineers would end up adding servers by hand under pressure, which is slow and error-prone.

Even Amazon faced this. On Prime Day 2018, internal documents reported by CNBC showed it did not have enough servers for the traffic surge. It switched to a scaled-down front page, temporarily cut off international traffic, and had engineers add servers manually while shoppers saw error pages for hours. The lesson for Onward is that capacity must grow automatically and be tested before the sale, not fixed by hand during it.

### Sources

- CNBC, "Amazon's internal documents show what caused the Prime Day crash" (19 July 2018): https://www.cnbc.com/2018/07/19/amazon-internal-documents-what-caused-prime-day-crash-company-scramble.html
- AWS, Target tracking scaling policies for Amazon EC2 Auto Scaling: https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scaling-target-tracking.html
- AWS, Dynamic scaling for Amazon EC2 Auto Scaling: https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-scale-based-on-demand.html
- AWS Well-Architected Framework, Reliability Pillar: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html
- AWS, What is AWS Systems Manager Session Manager: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html
- AWS, Amazon VPC pricing (NAT gateway): https://aws.amazon.com/vpc/pricing/

---

## 2. The business value of your solution

### Your chosen approach

I chose an Auto Scaling group of 2 to 6 small servers across two Availability Zones in eu-west-1 (Ireland), behind one Application Load Balancer. It scales on average CPU with a 50% target. It is the only option that handles both a planned sale and a surprise spike without anyone watching, and it keeps the site up if a server or a whole zone fails. Onward pays for extra servers only during the rush. A peak day costs about USD 5 against about USD 4 for a quiet day. Keeping six servers running all month would cost about three times as much in compute.

The servers are identical and disposable. Each one installs the order application from Git at a pinned version when it boots, so a replacement is always the same as the server it replaces. The whole environment is one CloudFormation template that Git sync deploys from GitHub, so every change is reviewed and the system can be rebuilt from the repository.

### Services you will use

| Service | The job it does | Why this service, used this way |
|---|---|---|
| Amazon VPC, public and private subnets in two Availability Zones | Separates the internet-facing load balancer from the servers. | Servers have no public address, so they cannot be reached from the internet, and two zones mean one data center failure does not stop orders. |
| Application Load Balancer | The single public address. It spreads requests across healthy servers and stops sending traffic to failed ones. | It is the only public resource. It checks `/health` on every server every 10 seconds and lets servers be added and removed without customers noticing. |
| Amazon EC2 Auto Scaling with a launch template (t3.micro, Amazon Linux 2023) | Keeps 2 to 6 servers running, adds servers when busy, removes them when quiet, and replaces unhealthy ones. | Target tracking at 50% average CPU follows real demand with one setting, and ELB health checks replace servers whose app is broken, not only crashed ones. The minimum of 2, one per zone, survives a zone loss; the maximum of 6 caps spend at three times normal capacity. |
| Amazon CloudWatch (1-minute monitoring and a dashboard) | Supplies the CPU metric that drives scaling, and shows servers, CPU and healthy hosts on one screen. | One-minute metrics let scaling react in minutes rather than 5-minute steps, for about USD 2 per server per month. |
| Regional NAT Gateway | Lets private servers download security updates, the app and packages, outbound only. | One managed gateway covers both zones, so there is no NAT server to patch and a zone outage does not cut off updates elsewhere. |
| AWS Systems Manager (Session Manager and Run Command) | Gives engineers a shell on servers and runs the time-limited CPU spike used to demonstrate scaling. | No SSH, no key pairs and no open admin ports. Every session and command is tied to a person's IAM identity and logged. |
| IAM role with an AWS managed policy | Gives servers only the permissions Systems Manager needs. | No stored credentials and no inline policies, which meets Onward's access standard. |
| Amazon EBS (encrypted gp3) | The disk for each server. | Encrypted by default and deleted with the server, so nothing is left behind after scale-in. |
| AWS CloudFormation with Git sync (AWS CodeConnections) | Builds and updates the whole environment from the GitHub repository. | Every change is a reviewed pull request, new app versions roll out one server at a time, and the stack can be deleted after a demo and rebuilt identically. |

### Who benefits, and how you will know

| Stakeholder | Benefit | How you would know |
|---|---|---|
| CTO | The order site stays up during sales-day peaks and when a server or zone fails, without anyone intervening. | During a 10-minute CPU spike, the group grows from 2 to about 4 servers within 3 to 5 minutes and shrinks back about 15 minutes after the spike ends. With one server terminated or one zone removed, the public address keeps answering with no failed requests. |
| Head of Operations | No one has to add or remove servers by hand on sales day. Failed servers are replaced automatically, and new versions roll out without downtime. | Zero manual scaling actions during a peak. A replacement server reaches InService on its own, and the dashboard shows desired and running servers matching throughout. |
| Head of Security | Only the load balancer is public. There are no admin ports or keys, and every admin action is logged. | Servers have no public IP, no security group allows port 22, no key pairs exist, IMDSv2 is required, and `scripts/demo/1-security-check.sh` passes. |
| Finance Lead | Extra capacity costs money only while it is used, with a known daily cost. | About USD 4.14 for a quiet day and USD 4.99 for a peak day (about USD 125 for a quiet month), against about USD 45 a month in compute alone if six servers ran all the time. |

### Limits and risks of your design

- **Scaling is not instant.** A new server takes about 3 to 5 minutes to boot and join. A spike steeper than that will slow responses briefly. For a known sale, the minimum can be raised beforehand.
- **Capacity is capped at 6 servers.** That covers three times normal demand. A bigger surge needs the maximum raised, which also raises the cost ceiling.
- **Servers depend on GitHub and the NAT gateway to boot.** If GitHub is unreachable, new servers cannot install the app, so scale-out and replacements fail. A pre-built server image (AMI) would remove this dependency later.
- **No HTTPS in dev.** There is no company domain or certificate yet, so traffic is plain HTTP. Production needs an ACM certificate and a port 443 listener.
- **No database.** The order desk is stateless, so any server can answer any request. Storing orders durably needs a shared database, which is a later step.
- **Single Region, no web application firewall.** A full Region outage would stop the site, and AWS WAF is not included to filter malicious traffic.
- **Fixed cost when idle.** The load balancer and NAT gateway bill by the hour, so dev stacks should be deleted after demos with `scripts/teardown.sh`.
- **Data residency unconfirmed.** Onward's legal team must confirm that customer data may be stored in Ireland before production use.
