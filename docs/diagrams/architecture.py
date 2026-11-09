"""Architecture diagram for the Onward sales-day order system, drawn with official AWS icons.

Regenerate (needs Graphviz and `pip install diagrams`), from the repository root:
    python docs/diagrams/architecture.py
Writes docs/images/architecture.png.
"""
import os

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import EC2, EC2AutoScaling
from diagrams.aws.general import User, Users
from diagrams.aws.management import Cloudformation, Cloudwatch, SystemsManager
from diagrams.aws.network import ElbApplicationLoadBalancer, InternetGateway, NATGateway
from diagrams.aws.security import IAMRole
from diagrams.onprem.vcs import Github

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "architecture")
FONT = "Noto Sans"


def group(border, bg="transparent", style="rounded", color=None):
    """Group box in the AWS architecture-icon colours."""
    return {
        "style": style, "pencolor": border, "bgcolor": bg, "penwidth": "1.6",
        "fontname": FONT, "fontsize": "14", "fontcolor": color or border,
        "labeljust": "l", "margin": "20",
    }


CLOUD = group("#232F3E")
REGION = group("#00A4A6", style="dashed,rounded")
VPC = group("#8C4FFF")
AZ = group("#147EBA", style="dashed,rounded")
PUBLIC = group("#7AA116", bg="#F2F6E8", color="#3B5310")
PRIVATE = group("#00A4A6", bg="#E6F6F7", color="#00585A")
ASG = group("#ED7100", style="dashed,rounded", color="#B45200")
NEUTRAL = group("#7D8998", bg="#F7F8F9", color="#545B64")


def edge(kind, label="", **extra):
    styles = {
        "traffic": dict(color="#ED7100", penwidth="2.2", fontcolor="#B45200"),
        "outbound": dict(color="#147EBA", penwidth="1.6", fontcolor="#0F5A85"),
        "mgmt": dict(color="#7D8998", style="dashed", penwidth="1.3", fontcolor="#545B64"),
        "invis": dict(style="invis"),
    }
    return Edge(label=label, fontname=FONT, fontsize="12", **styles[kind], **extra)


graph_attr = {
    "fontname": FONT, "fontsize": "26", "fontcolor": "#232F3E",
    "label": "Onward Logistics  |  Sales-day order system on Amazon EC2\n\n",
    "labelloc": "t", "labeljust": "c",
    "pad": "0.7", "nodesep": "0.55", "ranksep": "1.3",
    "splines": "spline", "bgcolor": "white", "newrank": "true",
}
node_attr = {"fontname": FONT, "fontsize": "13", "fontcolor": "#232F3E"}
TALL = {"height": "2.2", "imagepos": "tc"}   # square icons: keep the label clear of the icon

with Diagram("", filename=OUT, outformat="png", show=False, direction="LR",
             graph_attr=graph_attr, node_attr=node_attr):

    # ---------------------------------------------------------------- left: the public internet
    # Graphviz stacks nodes of the same column bottom-up here, so each group lists them bottom first.
    with Cluster("Internet", graph_attr=NEUTRAL):
        app_repo = Github("GitHub: app repo\n(Flask order app)")
        customers = Users("Merchants and\ncustomers")

    # ---------------------------------------------------------------- middle: AWS
    with Cluster("AWS Cloud", graph_attr=CLOUD):
        with Cluster("Region eu-west-1 (Ireland)", graph_attr=REGION):

            with Cluster("VPC onward-dev-vpc   10.30.0.0/16", graph_attr=VPC):
                igw = InternetGateway("Internet gateway")

                with Cluster("Public subnets  (AZ a + AZ b)", graph_attr=PUBLIC):
                    alb = ElbApplicationLoadBalancer("Application Load Balancer\nthe only public resource")

                nat = NATGateway("Regional NAT Gateway\noutbound only")

                with Cluster("Auto Scaling group   2 to 6 x t3.micro   target 50% CPU", graph_attr=ASG):
                    asg = EC2AutoScaling("EC2 Auto Scaling\nreplaces failed servers")
                    with Cluster("Availability Zone b", graph_attr=AZ):
                        with Cluster("Private subnet b", graph_attr=PRIVATE):
                            b2 = EC2("added on sales day", **TALL)
                            b1 = EC2("order server", **TALL)
                    with Cluster("Availability Zone a", graph_attr=AZ):
                        with Cluster("Private subnet a", graph_attr=PRIVATE):
                            a2 = EC2("added on sales day", **TALL)
                            a1 = EC2("order server", **TALL)

            with Cluster("Operations", graph_attr=NEUTRAL):
                ssm = SystemsManager("Systems Manager\nSession Manager, Run Command", **TALL)
                role = IAMRole("IAM server role\nmanaged policy only")
                cw = Cloudwatch("CloudWatch\n1-min metrics, dashboard", **TALL)
                cfn = Cloudformation("CloudFormation\nGit sync", **TALL)

    # ---------------------------------------------------------------- right: the team
    with Cluster("Engineering team", graph_attr=NEUTRAL):
        engineer = User("Engineer\n(IAM identity)")
        infra_repo = Github("GitHub: infrastructure repo\n(template + deployment file)")

    # Layout: left to right, without drawing anything
    for n in (a1, a2, b1, b2):
        n >> edge("invis") >> asg

    # Customer traffic, the only way in
    customers >> edge("traffic", "HTTP :80") >> igw
    igw >> edge("traffic") >> alb
    alb >> edge("traffic", ":8000, ALB security\ngroup only") >> [a1, b1]
    alb >> edge("traffic") >> [a2, b2]

    # Outbound only: security updates, packages and the app at boot
    igw >> edge("invis") >> nat   # keep the NAT gateway in the load balancer's column
    nat << edge("outbound") << asg
    igw << edge("outbound", "HTTPS out only") << nat
    app_repo << edge("outbound", "git clone app at\nAppVersion on boot") << igw

    # Deployment and operations
    cfn << edge("mgmt", "every commit") << infra_repo
    asg << edge("mgmt", "creates and updates\nthe stack") << cfn
    asg << edge("mgmt", "scale out / in") << cw
    ssm << edge("mgmt", "no SSH, no open ports") << engineer
    asg << edge("mgmt", "sessions and\nCPU-spike demo") << ssm
    asg << edge("mgmt", "attached to\nevery server") << role
