# AWS Dev Instance Cost Report

## Project Overview

This project automates the process of listing running Amazon EC2 instances in an authorized AWS development account. It filters instances by AWS tag and generates an estimated compute-cost summary.

## Features

- Lists running EC2 instances.
- Filters instances by tag key and value.
- Displays instance ID, name, instance type, and region.
- Estimates hourly and monthly compute costs.
- Exports results to a CSV report.
- Uses read-only EC2 permissions.

## Technologies

- Python 3
- Boto3
- Amazon EC2
- AWS CLI
- JSON and CSV
- Git and GitHub

## Project Structure

```text
aws-dev-instance-report/
├── list_dev_instances.py
├── rates.json
├── requirements.txt
├── README.md
└── .gitignore
```

## Prerequisites

- Python installed on Windows.
- Boto3 installed using `requirements.txt`.
- An AWS profile approved by your internship mentor.
- Permission to describe EC2 instances in the approved account.

## Installation

Create a virtual environment:

```powershell
python -m venv .venv
```

Install the dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Verify AWS Account

Use the AWS profile approved by your mentor:

```powershell
aws sts get-caller-identity --profile dev
```

Confirm that the account is correct before running the report. Do not use root credentials for routine development.

## Run the Script

```powershell
.\.venv\Scripts\python.exe list_dev_instances.py --profile dev --region ap-south-1
```

The default filter is:

`Environment=dev`

To filter by another tag:

```powershell
.\.venv\Scripts\python.exe list_dev_instances.py --profile dev --region ap-south-1 --tag-key Project --tag-value dev
```

Replace the profile and region with the values approved for your assignment.

## Output

The script creates:

`ec2-dev-report.csv`

The report contains matching instance details and estimated hourly and monthly costs.

Monthly estimates assume 730 hours per month.

## Cost Estimate Limitations

The rates in `rates.json` are illustrative placeholders, not verified AWS prices. Replace them with appropriate rates before using the estimates for planning.

These estimates are not actual AWS billing data. They exclude storage, data transfer, taxes, discounts, Savings Plans, Reserved Instances, and other charges.

Instance types without configured rates should be identified as `RATE_NOT_CONFIGURED`.

## IAM Permissions

The script requires read-only permission to describe EC2 instances. An administrator can grant this permission to an approved role or user:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ec2:DescribeInstances",
      "Resource": "*"
    }
  ]
}
```

Follow your organization's IAM approval process.

## Security

- Never commit AWS access keys or secret credentials.
- Do not commit private keys or `.env` files.
- Use an approved IAM role or profile.
- Do not commit generated reports unless your team approves them.

## Testing

1. Verify that only running instances matching the selected tag are returned.
2. Check the result when no instances match.
3. Verify the CSV headers and rows.
4. Check how unknown instance types are reported.
5. Confirm that the script does not create, modify, or terminate AWS resources.

Do not launch billable resources just to test the script.

## Author

Cloud & DevOps Internship Assignment