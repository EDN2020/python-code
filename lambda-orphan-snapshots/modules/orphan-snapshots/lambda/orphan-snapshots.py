import boto3
import os
from datetime import datetime

# Initialize the EC2 client
ec2_client = boto3.client('ec2')
current_time = datetime.now()
AGE_THRESHOLD = int(os.getenv('AGE_THRESHOLD', 90)) # If a value is not provide, in the variable, it defualts to 90 days

def send_html_email(orphan_snapshot_ids,context):
    region_name = context.invoked_function_arn.split(":")[3]
    account_id = context.invoked_function_arn.split(":")[4]
    SOURCE_EMAIL_ID = os.getenv('SOURCE_EMAIL_IDS')
    DESTINATION_EMAIL_IDS = os.getenv('DESTINATION_EMAIL_IDS').split(",") # We are accepting a list of emails
    ses_client = boto3.client("ses")
    CHARSET = "UTF-8"
    orphan_snapshot_ids_html = ""
    for snapshot in orphan_snapshot_ids:
      orphan_snapshot_ids_html += "<p>{}</p>".format(str(snapshot))
    HTML_EMAIL_CONTENT = """
        <html>
            <head></head>
            <h2 style='text-align:left'>Please find list of snapshots without volume attached </h2>
            <p>Account number : {}</p>
            <p>Region : {}</p>
            <p>Instance IDs :</p>
            {}
            </body>
        </html>
    """.format(account_id, region_name, orphan_snapshot_ids_html)

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
                "Data": "Orphan Snapshots to Delete",
            },
        },
        Source=SOURCE_EMAIL_ID,
    )
    print(response)

def get_orphan_snapshots(context):
    response = ec2_client.describe_snapshots(OwnerIds=['self'])
    orphan_snapshot_ids = []
    for snapshot in response['Snapshots']:
        snapshot_id = snapshot['SnapshotId'] 
        snapshot_start_time = snapshot['StartTime']
        snapshot_start_time_str = snapshot_start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        snapshot_start_datetime = datetime.strptime(snapshot_start_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        snapshot_age = (current_time - snapshot_start_datetime).days
        if snapshot_age > AGE_THRESHOLD:
            try:
                volume_id = snapshot.get('VolumeId')
                ec2_client.describe_volumes(VolumeIds=[volume_id])
            except ec2_client.exceptions.ClientError as e:
                orphan_snapshot_ids.append(snapshot_id)
                print(f"Snapshot ID: {snapshot_id} is attached to volume that does not exist")
    if len(orphan_snapshot_ids) != 0 :
        send_html_email(orphan_snapshot_ids,context)        

    return orphan_snapshot_ids


def delete_orphan_snapshots(snapshots):
    for snap_id in snapshots:
        response = ec2_client.delete_snapshot(
            SnapshotId=snap_id
        )
        print(response)
        try:
            status_code = response["ResponseMetadata"]["HTTPStatusCode"]
            if status_code == 200:
                status = "deleted"
            else:
                status = "Check the Console"
        except:
            print("did not get the status code")
            status = "Something went wrong"
        print(f"Snapshot ID: {snap_id}  status: {status}")    

def lambda_handler(event, context):
    get_orphan_snapshots(context)

    # orphan_snaps = get_orphan_snapshots()

    # delete_orphan_snapshots(orphan_snaps)