import argparse
import csv
import json
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def main():
    parser = argparse.ArgumentParser(
        description="List running EC2 instances matching a tag and estimate costs."
    )
    parser.add_argument("--profile", default="dev")
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--tag-key", default="Environment")
    parser.add_argument("--tag-value", default="dev")
    args = parser.parse_args()

    rates_path = Path(__file__).with_name("rates.json")

    try:
        with open(rates_path, encoding="utf-8") as file:
            rates = json.load(file)["hourly_usd_by_instance_type"]

        session = boto3.Session(profile_name=args.profile)
        ec2 = session.client("ec2", region_name=args.region)

        response = ec2.describe_instances(
            Filters=[
                {"Name": "instance-state-name", "Values": ["running"]},
                {"Name": f"tag:{args.tag_key}", "Values": [args.tag_value]},
            ]
        )

        instances = []

        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                tags = {
                    tag["Key"]: tag["Value"]
                    for tag in instance.get("Tags", [])
                }

                instance_type = instance["InstanceType"]
                hourly_rate = rates.get(instance_type)
                hourly_cost = (
                    float(hourly_rate) if hourly_rate is not None else None
                )

                instances.append({
                    "InstanceId": instance["InstanceId"],
                    "Name": tags.get("Name", ""),
                    "InstanceType": instance_type,
                    "State": instance["State"]["Name"],
                    "Region": args.region,
                    "HourlyEstimateUSD": (
                        f"{hourly_cost:.4f}"
                        if hourly_cost is not None else "RATE_NOT_CONFIGURED"
                    ),
                    "MonthlyEstimateUSD": (
                        f"{hourly_cost * 730:.2f}"
                        if hourly_cost is not None else "RATE_NOT_CONFIGURED"
                    ),
                })

        output_path = Path("ec2-dev-report.csv")
        columns = [
            "InstanceId", "Name", "InstanceType", "State",
            "Region", "HourlyEstimateUSD", "MonthlyEstimateUSD"
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(instances)

        known_hourly = sum(
            float(row["HourlyEstimateUSD"])
            for row in instances
            if row["HourlyEstimateUSD"] != "RATE_NOT_CONFIGURED"
        )

        print(f"Region: {args.region}")
        print(f"Filter: {args.tag_key}={args.tag_value}, state=running")
        print(f"Running instances found: {len(instances)}")
        print(f"Estimated hourly total: ${known_hourly:.4f} USD")
        print(f"Estimated monthly total: ${known_hourly * 730:.2f} USD")
        print(f"CSV report saved to: {output_path.resolve()}")
        print("Note: Estimates use rates.json and are not actual AWS billing.")

    except (OSError, ValueError, KeyError, BotoCoreError, ClientError) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()