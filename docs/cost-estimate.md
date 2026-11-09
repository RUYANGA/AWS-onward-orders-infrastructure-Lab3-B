# Cost estimate: onward-dev-orders (eu-west-1, Ireland)

On-demand list prices from the AWS Price List API, fetched 9 November 2026. They don't include
credits, Savings Plans or account-specific discounts. The line items are also in
[cost-estimate.csv](cost-estimate.csv).

**AWS Pricing Calculator estimate:** USD 129.35 a month, USD 1,552.20 for 12 months.
- Export: [cost-estimate-calculator.pdf](cost-estimate-calculator.pdf)
- Live estimate: https://calculator.aws/#/estimate?id=34490496cef73bdbbd0db75c2f11bd4879920187

See [Calculator result](#calculator-result) for how it matches the figures below.

## Summary

| Month | Servers | Estimated cost (USD) |
| --- | --- | --- |
| Quiet month | 2 servers all month | **128.96** |
| Busy month (4 sales days) | 2 servers, plus 4 extra for 8 hours on each sales day (6 in total) | **139.22** |

- **Most of the bill is fixed.** The NAT gateway across two zones, the load balancer hours and the
  four public IPv4 addresses cost USD 103.08 a month, 80% of a quiet month, whether or not anyone
  uses the site.
- **Sales days are cheap.** Four sales days add USD 10.26 to the month, about USD 2.57 each. A quiet day
  costs about USD 4.24 and a sales day about USD 6.80.
- **Scaling saves on compute.** Running 6 servers all month would cost USD 49.93 in EC2 alone, against
  USD 16.64 for the baseline of 2.
- **Delete the stack after demos.** `scripts/teardown.sh` removes everything that bills by the hour, and
  Git sync rebuilds it from the repository.

## Line items

| Service | Item | Quiet month | USD | Busy month | USD |
| --- | --- | --- | ---: | --- | ---: |
| Amazon EC2 | t3.micro Linux on-demand | 1,460 instance-hours | 16.64 | 1,588 instance-hours | 18.10 |
| Amazon EC2 | T3 Unlimited surplus CPU credits | 0 vCPU-hours | 0.00 | 154 vCPU-hours | 7.68 |
| Amazon EBS | gp3 root volumes, 8 GB each | 16.0 GB-month | 1.41 | 17.4 GB-month | 1.53 |
| Elastic Load Balancing | Application Load Balancer hours | 730 hours | 18.40 | 730 hours | 18.40 |
| Elastic Load Balancing | Load balancer capacity units (LCU) | 36.5 LCU-hours | 0.29 | 66.9 LCU-hours | 0.54 |
| Amazon VPC | Regional NAT Gateway, 2 Availability Zones | 1,460 AZ-hours | 70.08 | 1,460 AZ-hours | 70.08 |
| Amazon VPC | Regional NAT Gateway data processed | 3 GB | 0.14 | 11 GB | 0.53 |
| Amazon VPC | Public IPv4 addresses | 4 x 730 hours | 14.60 | 4 x 730 hours | 14.60 |
| Amazon CloudWatch | EC2 detailed monitoring (7 metrics per server) | 14.00 metric-months | 4.20 | 15.23 metric-months | 4.57 |
| Amazon CloudWatch | Target tracking alarms | 2 alarms | 0.20 | 2 alarms | 0.20 |
| Amazon CloudWatch | Dashboard | 1 dashboard | 3.00 | 1 dashboard | 3.00 |
| AWS Data Transfer | Out to the internet | 0 GB billable | 0.00 | 0 GB billable | 0.00 |
| AWS Systems Manager | Session Manager, Run Command | included | 0.00 | included | 0.00 |
| AWS CloudFormation | Git sync, CodeConnections | included | 0.00 | included | 0.00 |
| **Total** | | | **128.96** | | **139.22** |

## Prices used (eu-west-1)

| Item | Price List usage type | USD |
| --- | --- | ---: |
| EC2 t3.micro, Linux | `EU-BoxUsage:t3.micro` | 0.0114 per hour |
| T3 surplus CPU credits | `EU-CPUCredits:t3` | 0.05 per vCPU-hour |
| EBS gp3 storage | `EU-EBS:VolumeUsage.gp3` | 0.088 per GB-month |
| Application Load Balancer | `EU-LoadBalancerUsage` | 0.0252 per hour |
| Load balancer capacity unit | `EU-LCUUsage` | 0.008 per LCU-hour |
| Regional NAT Gateway | `EU-RegionalNatGateway-Hours` | 0.048 per hour, for each Availability Zone it serves |
| Regional NAT Gateway data | `EU-RegionalNatGateway-Bytes` | 0.048 per GB |
| Public IPv4 address | `EU-PublicIPv4:InUseAddress` | 0.005 per hour |
| CloudWatch metric | `EU-CW:MetricMonitorUsage` | 0.30 per metric-month (first 10,000) |
| CloudWatch alarm | `EU-CW:AlarmMonitorUsage` | 0.10 per alarm-month |
| CloudWatch dashboard | `DashboardsUsageHour-Basic` | 3.00 per dashboard-month |
| Data transfer out to the internet | `EU-DataTransfer-Out-Bytes` | 0.09 per GB, after 100 GB a month free |

Per [Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/), a NAT gateway with regional
availability is charged for each hour it is configured in each Availability Zone.

## Assumptions

- **Hours:** 730 hours in a month, the figure AWS uses.
- **Servers:** 2 run all month, one per zone. On each of 4 sales days a month, Auto Scaling adds 4 more for
  8 hours. That's 128 extra instance-hours.
- **CPU credits:** during sales days servers average 50% CPU, the scaling target. A t3.micro's baseline is
  10% per vCPU, so in unlimited mode the 40-point difference on 2 vCPUs is billed as surplus credits.
  This is an upper bound: credits the servers earn while quiet reduce it.
- **Public IPv4:** two addresses for the load balancer nodes and one per zone for the Regional NAT Gateway.
  Servers have no public IPs.
- **Load balancer traffic:** 0.05 LCU on a normal hour and 1 LCU during a sales-day hour, which is a small
  order site.
- **NAT data:** 3 GB a month for security updates and the app download at boot, plus 2 GB per sales day
  for the extra servers.
- **Data out to the internet:** 20 GB a month, or 40 GB with sales days. Both are inside the 100 GB a
  month free allowance.
- **CloudWatch:**
  - EC2 detailed monitoring sends 7 metrics per server, prorated by the hours each server runs.
  - Auto Scaling group metrics and load balancer metrics are free.
  - The dashboard is free if the account has 3 or fewer dashboards. It is counted here to be safe.
- **No charge:** Systems Manager Session Manager and Run Command, CloudFormation Git sync and AWS
  CodeConnections.

## Build the same estimate in the AWS Pricing Calculator

The AWS Pricing Calculator ([calculator.aws](https://calculator.aws/#/addService)) produces the
estimate file to hand in or share. Enter the quiet month below. The calculator's own rounding and
free-tier handling may move the total by a few dollars.

1. Open https://calculator.aws/#/addService and choose **Create estimate**.
2. **Amazon EC2:** search "EC2" and choose **Configure**.
   - Description: `Order servers (baseline)`
   - Region: **Europe (Ireland)**
   - Tenancy: **Shared Instances**, Operating system: **Linux**
   - Workload: **Constant usage**, **2** instances
   - Instance type: **t3.micro**, Pricing model: **On-Demand**
   - Amazon EBS: **General Purpose SSD (gp3)**, **8 GB** per instance
   - Monitoring: **Detailed monitoring**, if the form offers it. Otherwise, add it under CloudWatch in step 7.
   - Data transfer: outbound to the internet **20 GB per month**
   - Choose **Save and add service**.
3. **Amazon EC2, sales-day servers** (busy month only):
   - Description: `Order servers (sales days)`
   - Same settings as step 2, with **4** instances and usage of **32 hours per month** (4 sales days x 8 hours).
4. **Elastic Load Balancing:** choose **Application Load Balancer**.
   - Description: `Public load balancer`, Region: **Europe (Ireland)**
   - Number of Application Load Balancers: **1**
   - Processed bytes: **0.05 GB per hour**
   - Average new connections: **1 per second**, average connection duration: **1 second**
   - Average requests: **1 per second**, rule evaluations: **0**

   These inputs give about 0.05 LCU, as assumed above.
5. **Amazon VPC: NAT Gateway**
   - Description: `Regional NAT Gateway (2 AZs)`, Region: **Europe (Ireland)**
   - Number of NAT Gateways: **2**. The Regional NAT Gateway is billed once per zone it serves.
   - Data processed: **3 GB per month**
6. **Amazon VPC: public IPv4 addresses**
   - In-use public IPv4 addresses: **4**, for **730 hours**
7. **Amazon CloudWatch**
   - Region: **Europe (Ireland)**
   - Metrics: **14**, for 2 servers x 7 detailed monitoring metrics. Use **0** if detailed monitoring was
     already counted in step 2.
   - Dashboards: **1**
   - Standard resolution alarm metrics: **2**
8. Check that the total for the quiet month is about **USD 129**, and about **USD 139** with step 3 added.

### Calculator result

The estimate built in the AWS Pricing Calculator on 9 November 2026 (Europe (Ireland), On-Demand):

| Service | Description | Configuration | USD/month |
| --- | --- | --- | ---: |
| Amazon EC2 | Order servers - baseline (2 x t3.micro) | 2 x t3.micro, 100% of the month, 8 GB gp3, monitoring off, 20 GB out to the internet | 19.85 |
| Amazon EC2 | Order servers - sales days (4 extra x 8 h x 4 days) | 4 x t3.micro, 32 hours a month, 8 GB gp3 | 1.59 |
| Elastic Load Balancing | Public load balancer | 1 Application Load Balancer, 0.05 GB processed per hour | 18.69 |
| Amazon VPC | Network - Regional NAT Gateway and public IPv4 | 1 Regional NAT Gateway in 2 AZs, 3 GB processed, 4 in-use public IPv4 | 84.82 |
| Amazon CloudWatch | Monitoring - detailed metrics, dashboard, scaling alarms | 14 metrics, 1 dashboard, 2 standard alarms | 4.40 |
| **Total** | | | **129.35** (USD 1,552.20 for 12 months) |

This agrees with the quiet-month estimate above (USD 128.96) once three differences are counted:
- **+1.59:** the calculator estimate also includes the sales-day servers.
- **+1.80:** it charges the 20 GB of data out without the 100 GB free allowance.
- **−3.00:** it treats the dashboard as free.

The calculator has no field for T3 surplus CPU credits, which add up to USD 7.68 in a busy month.

### Export and share the estimate

- **Export:** the PDF exported from the calculator on 9 November 2026 is
  [cost-estimate-calculator.pdf](cost-estimate-calculator.pdf). To refresh it, open the estimate, choose
  **Export** and then **PDF**, and replace the file.
- **Share:** the estimate's public link is
  https://calculator.aws/#/estimate?id=34490496cef73bdbbd0db75c2f11bd4879920187. Opening it shows the same
  five services, and changes made there don't affect the saved PDF.
