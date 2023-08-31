import boto3
import email
import json
from email import policy
from base64 import b64decode
from botocore.exceptions import NoCredentialsError
from cryptography import x509
from cryptography.hazmat.backends import default_backend


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        email_file = response['Body'].read()
    except Exception as e:
        print(e)
        raise e
        
    format_certificate_signing_request(email_file)
    
def format_certificate_signing_request(email_file):

    message = email.message_from_bytes(email_file, policy=policy.default)

    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        filename = part.get_filename()
        if not filename:
            continue

        if part.get_content_type() == 'text/plain':
            print("Found text/plain attachment with filename: ", filename)
            content = part.get_payload(decode=True)
            print(content.decode())

        elif part.get_content_type() == 'application/pkcs10':
            print("Found application/pkcs10 attachment with filename: ", filename)
            content = part.get_payload(decode=True)
            print(content.decode())
            
        elif part.get_content_type() == 'application/octet-stream' and filename.endswith('.csr'):
            print("Found .csr file with filename: ", filename)
            content = part.get_payload(decode=True)

            csr = x509.load_pem_x509_csr(content, default_backend())

            domain_name = csr.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
            sans = check_for_sans(csr)
            full_csr = content.decode()
            
            
            # Debugging
            print(f"Domain name: {domain_name}")
            print(f"CSR: {full_csr}")

            if not csr.is_signature_valid:
                raise Exception("Signature is not valid")
            
            gandi_interaction_data = {
                "domain_name": domain_name,
                "csr": full_csr,
                "sans": sans
            }
            
            send_csr_to_gandi_lambda_function(gandi_interaction_data)
            
def check_for_sans(csr):
    try:
        san_extension = csr.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        sans = san_extension.value.get_values_for_type(x509.DNSName)
        print("Subject Alternative Names: ", sans)
        return sans
    except x509.extensions.ExtensionNotFound:
        print("No Subject Alternative Names found")
        return None
            
def send_csr_to_gandi_lambda_function(data):
    
    lambda_client = boto3.client('lambda')
    
    print(f"Sending data to Gandi Lambda function: {data}")
    
    try:
        csr_payload = json.dumps(data)
    except Exception as error:
        print(f"Error: {error}")
    
    response = lambda_client.invoke(
        FunctionName='operations-engineering-gandi-interaction',
        InvocationType='RequestResponse',
        Payload=csr_payload,
    )
    
    response_payload = json.loads(response['Payload'].read())
    
    print(f"Response Payload: {response_payload}")
