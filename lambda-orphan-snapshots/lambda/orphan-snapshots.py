import boto3
import os
from datetime import datetime

# Initialize the EC2 client
ec2_client = boto3.client('ec2')
current_time = datetime.now()
age_threshold = 90

def send_html_email(orphan_snapshot_ids,context):
    region_name = context.invoked_function_arn.split(":")[3]
    account_id = context.invoked_function_arn.split(":")[4]
    source_email_ids="eddiedanny2000@yahoo.com"
    destination_email_ids=["eddiedanny2000@yahoo.com"]
    ses_client = boto3.client("ses")
    CHARSET = "UTF-8"
    orphan_snapshot_ids_html = ""
    for snapshot in orphan_snapshot_ids:
      orphan_snapshot_ids_html += "<p>{}</p>".format(str(snapshot))
    HTML_EMAIL_CONTENT = """
        <html>
            <head></head>
            <h2 style='text-align:left'>Please find list of orphan snapshots without volume attached </h2>
            <p>Account number : {}</p>
            <p>Region : {}</p>
            <p>Instance IDs :</p>
            {}
            </body>
        </html>
    """.format(account_id, region_name, orphan_snapshot_ids_html)

    response = ses_client.send_email(
        Destination={
            "ToAddresses": destination_email_ids
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
        Source=source_email_ids,
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
        if snapshot_age > age_threshold:
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
    
### To Delete the snapshots, uncomment below two lines of code  
    # orphan_snaps = get_orphan_snapshots()
    # delete_orphan_snapshots(orphan_snaps)

## To test from your cli, uncomment below code
#     orphan_snaps = get_orphan_snapshots()
#     print(orphan_snaps)

# if __name__ == "__main__":
#     lambda_handler(event="", context="")