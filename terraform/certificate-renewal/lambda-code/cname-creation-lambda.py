import boto3
import json

client = boto3.client('route53')


def lambda_handler(event, context):

    domain_name = event['domain_name']
    dcv_subdomain = event['dcv_subdomain']
    dcv_value = event['dcv_value']

    hosted_zone_name = dcv_subdomain.split('.', 1)[1]

    hosted_zone_id = get_hosted_zone_id_from_hosted_zone_name(hosted_zone_name)

    create_cname_record_in_hosted_zone(
        hosted_zone_id, dcv_subdomain, dcv_value)

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully added CNAMEs to Route53')
    }


def get_hosted_zone_id_from_hosted_zone_name(hosted_zone_name):
    paginator = client.get_paginator('list_hosted_zones')

    for page in paginator.paginate():
        for zone in page['HostedZones']:
            if zone['Name'] == hosted_zone_name:
                return zone['Id']

    return None


def create_cname_record_in_hosted_zone(hosted_zone_id: str, record_name: str, record_value: str, ttl: int = 300):
    response = client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': 'CNAME',
                        'TTL': ttl,
                        'ResourceRecords': [{'Value': record_value}]
                    }
                }
            ]
        }
    )

    print(f"Reponse from Route53: {response}")
    return response
