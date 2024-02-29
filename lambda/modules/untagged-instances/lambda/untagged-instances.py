import boto3
import os

def send_html_email(instance_ids,context):
    region_name = context.invoked_function_arn.split(":")[3]
    account_id = context.invoked_function_arn.split(":")[4]
    SOURCE_EMAIL_ID = os.getenv('SOURCE_EMAIL_ID')
    DESTINATION_EMAIL_IDS = os.getenv('DESTINATION_EMAIL_IDS').split(",") # We are accepting a list of emails    
    ses_client = boto3.client("ses")
    CHARSET = "UTF-8"
    instance_ids_html = ""
    for i in instance_ids:
      instance_ids_html += "<p>{}</p>".format(str(i))
    HTML_EMAIL_CONTENT = """
        <html>
            <head></head>
            <h2 style='text-align:left'>Please find the list of instances without tag key equals Project </h2>
            <p>Account number : {}</p>
            <p>Region : {}</p>
            <p>Instance IDs :</p>
            {}
            </body>
        </html>
    """.format(account_id, region_name, instance_ids_html)

    response = ses_client.send_email(
        Destination={
            "ToAddresses": DESTINATION_EMAIL_IDS
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": CHARSET,
                    "Data": HTML_EMAIL_CONTENT,
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": "Instance To Monitor",
            },
        },
        Source=SOURCE_EMAIL_ID,
    )
    print(response)
# Initialize the EC2 client
ec2_client = boto3.client('ec2')
# Define the tag key you want to check for
tag_to_monitor = 'Project'
def get_instance_ids(ec2_client,context):
    response = ec2_client.describe_instances()
    instance_ids = []
    # Use describe_instances to get information about your instances
    response = ec2_client.describe_instances()
    # Iterate through the reservations and instances to find instances without the specified tag
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
                if 'Tags' in instance and str(tag_to_monitor) in str(instance['Tags']):
                    if str(tag_to_monitor) not in str(instance['Tags']):
                        instance_ids.append(instance['InstanceId'])
                        
                else:
                    instance_ids.append(instance['InstanceId'])
    if len(instance_ids) !=0 :
        send_html_email(instance_ids,context) 
        print(instance_ids)                
    return instance_ids


def lambda_handler(event, context):
    get_instance_ids(ec2_client,context)
