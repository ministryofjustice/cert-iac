import json
import http.client
import boto3
import time
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    
    api_key_dict = get_secret('operations-engineering-gandi-api-key', 'us-east-1')
    api_key = api_key_dict['operations-engineering-gandi-api-key']
    dcv_method = 'dns'
    
    domain_name = event['domain_name']
    csr = event['csr']
    subject_alternate_names = event['sans']
    
    certificate_list = get_certificate_list_with_http(api_key)
    
    certificate_id = get_certificate_id_from_domain_name(certificate_list, domain_name)
    
    dry_run_error = certificate_regeneration(certificate_id, csr, dcv_method, api_key, True)
    
    if dry_run_error:
        print(f"Error while performing a dry run: {dry_run_error}")
        
        return {
            'statusCode': 400,
            'body': json.dumps(dry_run_error)
        }
    else:
        real_run_error = certificate_regeneration(certificate_id, csr, dcv_method, api_key)
        
        if real_run_error:
            print(f"Error while performing a real run: {real_run_error}")
            
            return {
                'statusCode': 400,
                'body': json.dumps(real_run_error)
            }
            
    pending_certificate_id = get_pending_certificate_with_retry(certificate_list, domain_name)
            
    dcv_subdomain, dcv_value = get_dcv_details(pending_certificate_id, api_key, dcv_method)
    
    cname_creation_payload = {
        "domain_name": domain_name,
        "dcv_subdomain": dcv_subdomain,
        "dcv_value": dcv_value
    }
    
    send_data_to_cname_lambda_function(cname_creation_payload)

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully started the renewal process with Gandi')
    }
    
def certificate_regeneration(certificate_id:str, csr:str, dcv_method:str, api_key:str, dry_run:bool = False):
    
    conn = http.client.HTTPSConnection("api.gandi.net")

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }
    
    if dry_run:
        headers['Dry-Run'] = '1'
    

    # body = json.dumps({
    #     'csr': csr,
    #     'dcv_method': dcv_method
    # })
    
    body = json.dumps({
        'csr': csr,
        'dcv_method': dcv_method,
        'duration': 1
    })
    
    try:
        conn.request("P", f"/v5/certificate/issued-certs/{certificate_id}", body=body, headers=headers)
    except Exception as e:
        return f'An error occurred when attempting to regenerate the certificate: {str(e)}'

    response = conn.getresponse().read().decode("utf-8")
    print(f"Response from regenerating the certificate: {response}")

# def certificate_renewal_dry_run(certificate_id, csr, dcv_method, duration, api_key):
    
#     conn = http.client.HTTPSConnection("api.gandi.net")

#     headers = {
#         'Authorization': api_key,
#         'Content-Type': 'application/json',
#         'Dry-Run': '1'
#     }

#     body = json.dumps({
#         'csr': csr,
#         'dcv_method': dcv_method,
#         'duration': duration
#     })

#     conn.request("POST", f"/v5/certificate/issued-certs/{certificate_id}", body=body, headers=headers)

#     response = conn.getresponse()
#     read_response = response.read()

#     print(read_response.decode("utf-8"))

def get_pending_certificate_with_retry(certificate_list, domain_name, max_attempts=5, delay=10):
    for attempt in range(max_attempts):
        try:
            pending_certificate_id = get_certificate_id_from_domain_name(certificate_list, domain_name, True)
            if pending_certificate_id is not None:
                return pending_certificate_id
            else:
                print(f"No pending certificate found on attempt {attempt + 1}. Retrying in {delay} seconds...")
                
                time.sleep(delay)
        except Exception as e:
            print(f"An error occurred on attempt {attempt + 1}: {str(e)}. Retrying in {delay} seconds...")
            
            time.sleep(delay)
    
    raise Exception("Failed to retrieve a pending certificate after maximum attempts.")
    
def get_certificate_id_from_domain_name(certificate_list, domain_name:str, pending:bool = False):
    
    print(f"Getting the certificate ID...")

    certificate_json = json.loads(certificate_list)
    
    for certificate in certificate_json:
        if certificate['cn'] == domain_name and (not pending or certificate['status'] == 'pending'):
            return certificate['id']
            
    return None
    

def get_dcv_details(certificate_id, api_key, dcv_method):
    
    print(f"Getting DCV details...")
    
    conn = http.client.HTTPSConnection("api.gandi.net")

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }
    
    body = json.dumps({
        'dcv_method': dcv_method
    })
    
    try:
        conn.request("POST", f"/v5/certificate/issued-certs/{certificate_id}/dcv_params", body=body, headers=headers)
    except Exception as e:
        print(f"An error occured when retrieving the dcv details: {e}")

    response = json.loads(conn.getresponse().read().decode('utf-8'))
    
    dcv_subdomain, dcv_value = response.get('raw_messages')[0][0], response.get('raw_messages')[0][1], 
    
    
    print(f"dcv_subdomain: {dcv_subdomain}")
    print(f"dcv_value: {dcv_value}")
    
    return dcv_subdomain, dcv_value
    


def get_certificate_list_with_http(api_key):

    conn = http.client.HTTPSConnection("api.gandi.net")

    headers = { 'Authorization': api_key }
    conn.request("GET", "/v5/certificate/issued-certs?per_page=1000", headers=headers)

    res = conn.getresponse()
    
    data = res.read()

    return data.decode("utf-8")
    
            
def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise Exception(f"Error retrieving secret: {e.response['Error']['Message']}") from e

    else:
        if 'SecretString' in get_secret_value_response:
            secret_dict = json.loads(get_secret_value_response['SecretString'])
        else:
            secret_dict = json.loads(base64.b64decode(get_secret_value_response['SecretBinary']))
        
    return secret_dict
    
    
def send_data_to_cname_lambda_function(cname_creation_payload):
    
    lambda_client = boto3.client('lambda')
    
    print(f"Data going to CNAME Lambda function: {cname_creation_payload}")
    
    try:
        cname_payload = json.dumps(cname_creation_payload)
    except Exception as error:
        print(f"Error: {error}")
    
    response = lambda_client.invoke(
        FunctionName='operations-engineering-cname-creation',
        InvocationType='RequestResponse',
        Payload=cname_payload,
    )
    
    response_payload = json.loads(response['Payload'].read())
    
    print(f"Response Payload: {response_payload}")
