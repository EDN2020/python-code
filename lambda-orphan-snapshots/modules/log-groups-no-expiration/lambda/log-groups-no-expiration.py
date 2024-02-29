import boto3
import os
def send_html_email(log_groups_with_never_expire,context):
    SOURCE_EMAIL_ID = os.getenv('SOURCE_EMAIL_ID')
    DESTINATION_EMAIL_IDS = os.getenv('DESTINATION_EMAIL_IDS').split(",") # We are accepting a list of emails
    ses_client = boto3.client("ses")
    region_name = context.invoked_function_arn.split(":")[3]
    account_id = context.invoked_function_arn.split(":")[4]
    CHARSET = "UTF-8"
    logs=""
    for log in log_groups_with_never_expire:
      logs += "<p>{}</p>".format(str(log))
    HTML_EMAIL_CONTENT = """
        <html>
                <head></head>
                <h2 style='text-align:left'>Log Groups with infinite retention in </h2>
                <p>Account number : {}</p>
                <p>Region : {}</p>
                <p>Log Groups :</p>
                {}
                </body>
            </html>
    """.format(account_id, region_name, logs)
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
                "Data": "Log Groups with infinite retention in {} / {}".format(account_id,region_name),
            },
        },
        Source=SOURCE_EMAIL_ID,
    )
    print(response)
def get_log_groups_with_never_expire(client,group_names,context):
    """Return a list containing the names of all Never Expire log groups."""
    log_groups_with_never_expire=[]
    for group_name in group_names:
        response = client.describe_log_groups(logGroupNamePrefix=group_name)
        # print(response["logGroups"])
        for i in response["logGroups"]:
            if "retentionInDays" not in i:
                log_groups_with_never_expire.append(i['logGroupName'])
    if len(log_groups_with_never_expire) != 0 :
        send_html_email(log_groups_with_never_expire,context)
    print("list of log groups with never expire retention")
    print(log_groups_with_never_expire)
    print(len(log_groups_with_never_expire))
def get_log_groups(context):
    """Return a list containing the names of all log groups."""
    client = boto3.client('logs')
    found_all = False
    next_token = None
    group_names = []
    while not found_all:
        if next_token is not None:
            response = client.describe_log_groups(nextToken=next_token)
        else:
            response = client.describe_log_groups()
        if 'logGroups' in response:
            for group in response['logGroups']:
                if 'logGroupName' in group:
                    group_names.append(group['logGroupName'])
        next_token = response.get('nextToken', None)
        if next_token is None:
            found_all = True
    get_log_groups_with_never_expire(client,group_names,context)
    return group_names

# Main handler for this script.
def lambda_handler(event, context):
    get_log_groups(context)
