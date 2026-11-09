"""Architecture diagram for the Onward sales-day order system (stack onward-dev-orders).

Drawn as SVG with exact coordinates in the AWS architecture-diagram style (official AWS
icons, AWS group colours, orthogonal connectors), then rendered to PNG.

Regenerate from the repository root (needs `pip install diagrams cairosvg`; the AWS icons
come from the diagrams package):
    python docs/diagrams/architecture.py
Writes docs/images/architecture.svg and docs/images/architecture.png.
"""
import base64
import os
from html import escape

import cairosvg
import diagrams

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "images", "architecture")
ICONS = os.path.join(os.path.dirname(os.path.dirname(diagrams.__file__)), "resources")
FONT = "Liberation Sans, Arial, Helvetica, sans-serif"

W, H = 2240, 1760
INK, GREY = "#232F3E", "#545B64"
DARK, PURPLE, PINK = "#232F3E", "#8C4FFF", "#E7157B"

svg = []


def add(s):
    svg.append(s)


# ------------------------------------------------------------------ primitives
def text(x, y, lines, size=13, color=INK, anchor="start", weight="normal", bg=False):
    lines = lines.split("\n") if isinstance(lines, str) else lines
    lh = size * 1.25
    if bg:
        w = max(len(l) for l in lines) * size * 0.53 + 8
        h = lh * len(lines) + 2
        x0 = {"start": x - 4, "middle": x - w / 2, "end": x - w + 4}[anchor]
        add(f'<rect x="{x0:.1f}" y="{y - size - 1:.1f}" width="{w:.1f}" height="{h:.1f}" fill="white"/>')
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{escape(l)}</tspan>' for i, l in enumerate(lines))
    add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{color}" '
        f'text-anchor="{anchor}" font-weight="{weight}">{spans}</text>')


def icon(path, cx, cy, size=64, opacity=1.0):
    with open(os.path.join(ICONS, path), "rb") as f:
        data = base64.b64encode(f.read()).decode()
    add(f'<image x="{cx - size / 2}" y="{cy - size / 2}" width="{size}" height="{size}" opacity="{opacity}" '
        f'href="data:image/png;base64,{data}"/>')


def badge(x, y, color, glyph):
    """32x32 group icon in the top-left corner of a group, like the AWS group shapes."""
    add(f'<rect x="{x}" y="{y}" width="32" height="32" fill="{color}"/>')
    s = 'fill="none" stroke="white" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"'
    g = {
        "aws": f'<text x="{x + 16}" y="{y + 19}" font-family="{FONT}" font-size="12" font-weight="bold" '
               f'fill="white" text-anchor="middle">aws</text>'
               f'<path d="M{x + 7} {y + 23} q9 5 18 0" {s}/>',
        "flag": f'<path d="M{x + 10} {y + 25} V{y + 7} H{x + 23} l-3 4 l3 4 H{x + 10}" {s}/>',
        "cloud": f'<path d="M{x + 9} {y + 22} h14 a4.5 4.5 0 0 0 0 -9 a6 6 0 0 0 -11 -1 a4.5 4.5 0 0 0 -3 10 z" {s}/>'
                 f'<rect x="{x + 13}" y="{y + 17}" width="6" height="5" {s}/>',
        "lock": f'<rect x="{x + 10}" y="{y + 15}" width="12" height="10" {s}/>'
                f'<path d="M{x + 12.5} {y + 15} v-3 a3.5 3.5 0 0 1 7 0 v3" {s}/>',
        "scale": f'<rect x="{x + 12}" y="{y + 12}" width="8" height="8" {s}/>'
                 f'<path d="M{x + 16} {y + 5} v5 M{x + 16} {y + 27} v-5 M{x + 5} {y + 16} h5 M{x + 27} {y + 16} h-5 '
                 f'M{x + 14} {y + 7} l2 -2 l2 2 M{x + 14} {y + 25} l2 2 l2 -2 M{x + 7} {y + 14} l-2 2 l2 2 '
                 f'M{x + 25} {y + 14} l2 2 l-2 2" {s}/>',
    }[glyph]
    add(g)


def group(x, y, w, h, label, stroke, fill="none", font=None, dashed=False, glyph=None,
          bold=True, center=False):
    dash = ' stroke-dasharray="6,4"' if dashed else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{1.5 if fill == "none" else 0}"{dash}/>')
    if glyph:
        badge(x, y, stroke, glyph)
    tx = x + w / 2 if center else x + (40 if glyph else 10)
    text(tx, y + 21, label, size=14, color=font or stroke, weight="bold" if bold else "normal",
         anchor="middle" if center else "start")


def wire(points, color, dashed=False, label=None, at=None, anchor="middle", lcolor=None, r=10, arrow=True):
    """Orthogonal connector with rounded corners and an arrowhead at the end."""
    d = f"M{points[0][0]} {points[0][1]}"
    for i in range(1, len(points) - 1):
        (x0, y0), (x1, y1), (x2, y2) = points[i - 1], points[i], points[i + 1]
        def toward(ax, ay, bx, by, dist):
            length = max(abs(bx - ax), abs(by - ay)) or 1
            k = min(dist, length / 2) / length
            return ax + (bx - ax) * k, ay + (by - ay) * k
        p = toward(x1, y1, x0, y0, r)
        q = toward(x1, y1, x2, y2, r)
        d += f" L{p[0]:.1f} {p[1]:.1f} Q{x1} {y1} {q[0]:.1f} {q[1]:.1f}"
    d += f" L{points[-1][0]} {points[-1][1]}"
    dash = ' stroke-dasharray="8,6"' if dashed else ""
    mid = {DARK: "dark", PURPLE: "purple", PINK: "pink"}[color]
    head = f' marker-end="url(#arrow-{mid})"' if arrow else ""
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"{dash}{head}/>')
    if label:
        text(at[0], at[1], label, size=12, color=lcolor or color, anchor=anchor, bg=True)


# ------------------------------------------------------------------ canvas
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add("<defs>" + "".join(
    f'<marker id="arrow-{n}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
    f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
    for n, c in (("dark", DARK), ("purple", PURPLE), ("pink", PINK))) + "</defs>")
add(f'<rect width="{W}" height="{H}" fill="white"/>')

text(20, 42, "Onward Logistics: onward-dev order system", size=26, weight="bold")
text(20, 68, "Stack onward-dev-orders, created from templates/orders.yaml by CloudFormation Git sync", size=15, color=GREY)

# ------------------------------------------------------------------ groups
group(20, 160, 2015, 1395, "AWS Cloud", DARK, glyph="aws")
group(55, 210, 1945, 1305, "eu-west-1 (Ireland)", "#00A4A6", font="#147EBA", dashed=True, glyph="flag")
group(90, 290, 1420, 1185, "VPC onward-dev-vpc 10.30.0.0/16", PURPLE, font="#AAB7B8", glyph="cloud")

AZ_Y, AZ_H = 370, 1010
for x, az, s in ((125, "A", "a"), (815, "B", "b")):
    group(x, AZ_Y, 660, AZ_H, f"Availability Zone {az}", "#147EBA", dashed=True, center=True)
    pub = "10.30.0.0/24" if s == "a" else "10.30.1.0/24"
    prv = "10.30.2.0/24" if s == "a" else "10.30.3.0/24"
    group(x + 25, 420, 610, 230, f"Public subnet public-{s} {pub}", "#7AA116",
          fill="#F2F6E8", font="#248814", glyph="lock")
    group(x + 25, 700, 610, 650, f"Private subnet private-{s} {prv}", "#00A4A6",
          fill="#E6F6F7", font="#147EBA", glyph="lock")

# Auto Scaling group across both private subnets
add('<rect x="175" y="760" width="1250" height="520" fill="none" stroke="#D86613" stroke-width="1.5" '
    'stroke-dasharray="6,4"/>')
badge(175, 760, "#ED7100", "scale")
text(800, 783, "Auto Scaling group onward-dev-orders: 2 to 6 x t3.micro, target 50% average CPU, ELB health checks",
     size=14, color="#D86613", anchor="middle", weight="bold")

# ------------------------------------------------------------------ nodes
icon("aws/general/users.png", 800, 52, 64)
text(840, 58, "Merchants and customers", size=15)

icon("aws/network/internet-gateway.png", 800, 290, 62)
text(840, 284, "Internet gateway\nonward-dev-igw", size=14)

icon("aws/network/elb-application-load-balancer.png", 800, 495, 66)
text(800, 552, "Application Load Balancer\nonward-dev-orders (nodes in both AZs)\nthe only public resource",
     size=14, anchor="middle", bg=True)

SERVER_Y = 900
servers = {}
for s, base in (("a", 125), ("b", 815)):
    main_x, extra_x = base + 420, base + 560
    icon("aws/compute/ec2-instance.png", main_x, SERVER_Y, 64)
    text(main_x - 42, SERVER_Y - 4, "Order server\nFlask :8000", size=14, anchor="end")
    icon("aws/compute/ec2-instance.png", extra_x, SERVER_Y, 64, opacity=0.45)
    text(extra_x, SERVER_Y + 54, "Extra server\n(sales day)", size=14, color=GREY, anchor="middle")
    servers[s] = (main_x, extra_x)

icon("aws/network/nat-gateway.png", 800, 1428, 62)
text(840, 1414, "Regional NAT Gateway onward-dev-nat\nspans both AZs, outbound only", size=14)

RIGHT_X = 1650
icon("aws/management/cloudformation.png", RIGHT_X, 345, 70)
text(RIGHT_X, 405, "CloudFormation\nGit sync", size=14, anchor="middle")
icon("aws/management/systems-manager.png", RIGHT_X, 700, 70)
text(RIGHT_X, 760, "Systems Manager\nSession Manager, Run Command", size=14, anchor="middle")
icon("aws/management/cloudwatch.png", RIGHT_X, 1020, 70)
text(RIGHT_X, 1100, "CloudWatch\n1-minute metrics, dashboard", size=14, anchor="middle")
icon("aws/security/identity-and-access-management-iam.png", RIGHT_X, 1290, 70)
text(RIGHT_X, 1350, "IAM server role\nAWS managed policy only", size=14, anchor="middle")

FAR_X = 2160
icon("onprem/vcs/github.png", FAR_X, 345, 64)
text(FAR_X, 400, "GitHub infrastructure\nrepo, main branch", size=14, anchor="middle")
icon("aws/general/user.png", FAR_X, 700, 64)
text(FAR_X, 755, "Engineers\n(IAM identity)", size=14, anchor="middle")
icon("onprem/vcs/github.png", FAR_X, 1428, 64)
text(FAR_X, 1483, "GitHub app repo\n(Flask order app)", size=14, anchor="middle")

# ------------------------------------------------------------------ connectors
# Inbound: the only way in
wire([(800, 86), (800, 256)], DARK, label="HTTP 80", at=(800, 168))
wire([(800, 323), (800, 459)], DARK)
for s, side in (("a", -1), ("b", 1)):
    main_x, extra_x = servers[s]
    start = 768 if s == "a" else 832
    wire([(start, 515), (main_x, 515), (main_x, SERVER_Y - 33)], DARK)
    wire([(start, 515), (extra_x, 515), (extra_x, SERVER_Y - 33)], DARK)
for x in (servers["a"][0], servers["b"][0]):
    text(x, 670, "HTTP 8000\nonward-dev-alb -> onward-dev-orders-servers", size=12, anchor="middle", bg=True)

# Outbound only, through the Regional NAT Gateway
BUS_Y = 1215
# Each zone has one outbound bus; both buses meet between the zones and drop to the NAT gateway.
# Zone A: the bus starts under the order server and the extra server joins it from the right.
main_x, extra_x = servers["a"]
wire([(main_x, SERVER_Y + 34), (main_x, BUS_Y), (800, BUS_Y)], PURPLE, dashed=True, arrow=False)
wire([(extra_x + 34, SERVER_Y), (extra_x + 70, SERVER_Y), (extra_x + 70, BUS_Y)], PURPLE, dashed=True, arrow=False)
text((main_x + extra_x) / 2, BUS_Y + 4, "outbound 443", size=12, color=PURPLE, anchor="middle", bg=True)
# Zone B: the extra server drops between the two servers, and the bus starts there.
main_x, extra_x = servers["b"]
drop = (main_x + extra_x) / 2
wire([(extra_x - 34, SERVER_Y), (drop, SERVER_Y), (drop, BUS_Y), (800, BUS_Y)], PURPLE, dashed=True, arrow=False)
wire([(main_x, SERVER_Y + 34), (main_x, BUS_Y)], PURPLE, dashed=True, arrow=False)
text((800 + main_x) / 2, BUS_Y + 4, "outbound 443", size=12, color=PURPLE, anchor="middle", bg=True)
wire([(800, BUS_Y), (800, 1396)], PURPLE, dashed=True)
wire([(832, 1440), (FAR_X - 40, 1440)], PURPLE, dashed=True,
     label="HTTPS 443 through the internet gateway: dnf security updates, git clone app at AppVersion",
     at=(1480, 1444))

# Management and platform services
wire([(FAR_X - 36, 345), (RIGHT_X + 40, 345)], PINK, dashed=True, label="commit -> Git sync", at=(1905, 349))
wire([(RIGHT_X - 40, 345), (1512, 345)], PINK, dashed=True, label="deploys stack", at=(1562, 374))
wire([(FAR_X - 36, 700), (RIGHT_X + 40, 700)], PINK, dashed=True, label="IAM + ssm:StartSession", at=(1905, 704))
wire([(RIGHT_X - 40, 700), (1470, 700), (1470, 840), (1427, 840)], PINK, dashed=True,
     label="sessions and CPU-spike demo over the\nagent's outbound link, no inbound port", at=(1612, 822))
wire([(1427, 990), (RIGHT_X - 40, 990)], PINK, dashed=True, label="CPU metrics", at=(1530, 980))
wire([(RIGHT_X - 40, 1050), (1427, 1050)], PINK, dashed=True, label="scale out / in", at=(1522, 1072))

# ------------------------------------------------------------------ legend
add('<rect x="20" y="1590" width="1320" height="150" rx="14" fill="#F6F8FB" stroke="#D5DBE3"/>')
text(36, 1618, "Legend", size=15, weight="bold")
for i, (color, dashed, words) in enumerate((
        (DARK, False, "allowed inbound traffic and the security group rule that allows it"),
        (PURPLE, True, "outbound only: updates, the app download and AWS APIs, through the Regional NAT Gateway"),
        (PINK, True, "deployment, management and platform services"))):
    y = 1643 + i * 22
    dash = ' stroke-dasharray="5,3"' if dashed else ""
    add(f'<line x1="36" y1="{y - 5}" x2="60" y2="{y - 5}" stroke="{color}" stroke-width="2.5"{dash}/>')
    text(68, y, words, size=14)
text(36, 1712, "Faded servers are added by Auto Scaling on sales days and removed afterwards (2 to 6 in total).",
     size=14)
text(36, 1732, "No port 22 rule and no key pairs exist. Servers have no public IPs. Private subnets have no "
     "inbound route from the internet.", size=14, weight="bold")

add("</svg>")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT + ".svg", "w") as f:
    f.write("\n".join(svg))
cairosvg.svg2png(url=OUT + ".svg", write_to=OUT + ".png", output_width=W * 1.5, background_color="white")
print("wrote", os.path.relpath(OUT + ".png"))
