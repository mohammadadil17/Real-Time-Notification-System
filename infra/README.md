# AWS deployment

Deploys the same stack we run locally onto AWS, split into two tiers:

- **Data tier** — one EC2 instance (`t3.small`), not auto-scaled, running
  Postgres + Redis + Kafka via the same `docker-compose.yml` as local dev
  (just a different subset of services). Holds state, so it isn't a
  candidate for horizontal scaling the way the app tier is.
- **App tier** — an Auto Scaling Group of EC2 instances (`t3.micro` by
  default, min 1 / max 3, target-tracking on CPU) running the FastAPI app,
  the Kafka consumer, and the digest worker, behind an Application Load
  Balancer that health-checks `/health`.

Both tiers clone this repo via `git clone` and build the Docker image
on-instance at boot — no container registry (ECR) involved. That's a
deliberate simplification for a portfolio deploy; see **Known limitations**
below for what a production version would do instead.

## Cost warning

**This is not free.** Left running continuously, rough order of magnitude in
`us-east-1` (check the [AWS Pricing Calculator](https://calculator.aws) for
current numbers — this will drift):

| Resource | ~Monthly |
|---|---|
| Data instance (t3.small) | ~$15 |
| App instance (t3.micro × 1 desired) | ~$8 |
| Application Load Balancer | ~$16 (fixed, even near-idle) |
| EBS volumes, data transfer | a few $ |
| **Total, idle** | **~$40-45/mo** |

Scaling out under load (Locust, demoing autoscaling) adds cost proportional
to however many extra `t3.micro` instances the ASG launches, only while
they're running. **Run `terraform destroy` when you're not actively using
this** — see Teardown below.

## Prerequisites

1. An AWS account, and the AWS CLI configured with credentials that can
   create VPC/EC2/IAM/ELB/ASG resources:
   ```
   aws configure
   ```
2. Terraform (already installed locally in this session via
   `brew install hashicorp/tap/terraform`).
3. The [Session Manager plugin for the AWS CLI](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
   if you want a shell on an instance for debugging (no SSH key is set up —
   see **Debugging access** below).

## Configure secrets

`jwt_secret_key` has no default on purpose — the local dev placeholder
(`change-me-in-env`) must never sign real tokens. Generate a real one and
put it in a `terraform.tfvars` file (already gitignored, never commit it):

```
cd infra
echo "jwt_secret_key = \"$(openssl rand -hex 32)\"" > terraform.tfvars
```

## Deploy

```
cd infra
terraform init
terraform plan     # review what it's about to create
terraform apply     # type "yes" to confirm
```

`terraform apply` takes a few minutes — it's waiting on the data instance's
user-data to finish (install Docker, clone the repo, bring up
Postgres/Redis/Kafka, run migrations) before the app tier's launch template
can point at its private IP.

When it finishes:

```
terraform output alb_dns_name
curl http://<alb_dns_name>/health
```

## Load-testing the deployment

Point the same Locust file we used locally at the ALB instead:

```
cd ../loadtest
locust -f locustfile.py --host http://<alb_dns_name>
```

Open the Locust web UI, ramp up users, and watch the app tier's CPU climb in
the EC2 console — the Auto Scaling Group's target-tracking policy should
launch additional `t3.micro` instances once average CPU crosses the
configured target (50% by default), and the ALB's target group should pick
them up automatically once their `/health` check passes.

## Debugging access

No SSH key pair is provisioned — instances are reached via SSM Session
Manager instead (no open port 22, no key to lose):

```
aws ssm start-session --target $(terraform output -raw data_instance_id)
```

Once connected: `cd /opt/app && docker compose logs -f kafka` (or whichever
service). For an app-tier instance, find its instance ID in the EC2 console
(tagged `notif-app`) and use the same command.

## Teardown

```
terraform destroy
```

Confirm with `yes`. This deletes everything Terraform created — the data
instance's Postgres data goes with it (see Known limitations).

## Known limitations

Deliberate simplifications for a portfolio deploy, with what a production
version would do instead:

- **No HTTPS.** The ALB listens on plain HTTP:80. Adding HTTPS needs a real
  domain name and an ACM certificate, both out of scope here.
- **No NAT gateway / private subnets.** Everything sits in public subnets;
  security groups (not network isolation) are what actually restrict access.
  A NAT gateway has its own hourly cost that isn't worth it for a demo.
- **No managed data services.** Postgres/Redis/Kafka are self-hosted on one
  EC2 instance rather than RDS/ElastiCache/MSK — no automated backups,
  Multi-AZ failover, or patching. Destroying the data instance (or
  `terraform destroy`) loses all data permanently.
- **Images are built from source on every instance boot**, not pulled from a
  registry. Fine at this scale; a real deploy pipeline would build once,
  push to ECR, and have instances `docker pull` a tagged image instead of
  each one running its own `docker compose build`.
- **No CloudWatch alarms/dashboards** beyond what the ALB health check and
  ASG scaling policy already imply.
