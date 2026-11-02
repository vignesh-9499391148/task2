import argparse
import csv
import json
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


SAMPLE_INSTANCES = [
    {
        "InstanceId": "i-0123456789abcdef0",
        "InstanceType": "t3.micro",
        "State": {"Name": "running"},
        "Tags": [
            {"Key": "Name", "Value": "Dev-Web-Server"},
            {"Key": "Environment", "Value": "dev"},
        ],
    },
    {
        "InstanceId": "i-0234567890abcdef1",
        "InstanceType": "t3.small",
        "State": {"Name": "running"},
        "Tags": [
            {"Key": "Name", "Value": "Dev-App-Server"},
            {"Key": "Environment", "Value": "dev"},
        ],
    },
    {
        "InstanceId": "i-0345678901abcdef2",
        "InstanceType": "t3.medium",
        "State": {"Name": "running"},
        "Tags": [
            {"Key": "Name", "Value": "Dev-Test-Server"},
            {"Key": "Environment", "Value": "dev"},
        ],
    },
    {
        "InstanceId": "i-0456789012abcdef3",
        "InstanceType": "t3.micro",
        "State": {"Name": "stopped"},
        "Tags": [
            {"Key": "Name", "Value": "Stopped-Server"},
            {"Key": "Environment", "Value": "dev"},
        ],
    },
    {
        "InstanceId": "i-0567890123abcdef4",
        "InstanceType": "t3.small",
        "State": {"Name": "running"},
        "Tags": [
            {"Key": "Name", "Value": "Production-Server"},
            {"Key": "Environment", "Value": "prod"},
        ],
    },
]


def main():
    parser = argparse.ArgumentParser(
        description="Report running EC2 instances and estimate compute costs."
    )
    parser.add_argument("--profile", default="dev")
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--tag-key", default="Environment")
    parser.add_argument("--tag-value", default="dev")
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Use fictional EC2 data without connecting to AWS.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    rates_path = base_dir / "rates.json"
    output_path = base_dir / "ec2-dev-report.csv"

    try:
        with rates_path.open(encoding="utf-8") as file:
            rates = json.load(file)["hourly_usd_by_instance_type"]

        if args.sample_data:
            # Offline mode: no AWS API calls or credentials needed.
            all_instances = SAMPLE_INSTANCES
            print("MODE: SAMPLE DATA (no AWS connection)")
        else:
            session = boto3.Session(profile_name=args.profile)
            ec2 = session.client("ec2", region_name=args.region)

            paginator = ec2.get_paginator("describe_instances")
            all_instances = []

            pages = paginator.paginate(
                Filters=[
                    {
                        "Name": "instance-state-name",
                        "Values": ["running"],
                    },
                    {
                        "Name": f"tag:{args.tag_key}",
                        "Values": [args.tag_value],
                    },
                ]
            )

            for page in pages:
                for reservation in page["Reservations"]:
                    all_instances.extend(reservation["Instances"])

            print("MODE: AWS")

        rows = []

        for instance in all_instances:
            tags = {
                tag["Key"]: tag["Value"]
                for tag in instance.get("Tags", [])
            }

            # Apply filters in sample mode too.
            if instance["State"]["Name"] != "running":
                continue
            if tags.get(args.tag_key) != args.tag_value:
                continue

            instance_type = instance["InstanceType"]
            rate = rates.get(instance_type)
            hourly_cost = float(rate) if rate is not None else None

            rows.append({
                "InstanceId": instance["InstanceId"],
                "Name": tags.get("Name", ""),
                "InstanceType": instance_type,
                "State": instance["State"]["Name"],
                "Region": args.region,
                "HourlyEstimateUSD": (
                    f"{hourly_cost:.4f}"
                    if hourly_cost is not None
                    else "RATE_NOT_CONFIGURED"
                ),
                "MonthlyEstimateUSD": (
                    f"{hourly_cost * 730:.2f}"
                    if hourly_cost is not None
                    else "RATE_NOT_CONFIGURED"
                ),
            })

        columns = [
            "InstanceId",
            "Name",
            "InstanceType",
            "State",
            "Region",
            "HourlyEstimateUSD",
            "MonthlyEstimateUSD",
        ]

        with output_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

        known_hourly = sum(
            float(row["HourlyEstimateUSD"])
            for row in rows
            if row["HourlyEstimateUSD"] != "RATE_NOT_CONFIGURED"
        )

        unknown_count = sum(
            row["HourlyEstimateUSD"] == "RATE_NOT_CONFIGURED"
            for row in rows
        )

        print(f"Region: {args.region}")
        print(f"Filter: {args.tag_key}={args.tag_value}, state=running")
        print(f"Matching running instances: {len(rows)}")
        print(f"Estimated hourly total: ${known_hourly:.4f} USD")
        print(f"Estimated monthly total: ${known_hourly * 730:.2f} USD")
        print(f"Instances without configured rates: {unknown_count}")
        print(f"CSV report saved to: {output_path}")
        print("Cost estimates use rates.json; they are not actual AWS bills.")

    except (OSError, ValueError, KeyError, BotoCoreError, ClientError) as error:
        print(f"Error: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
