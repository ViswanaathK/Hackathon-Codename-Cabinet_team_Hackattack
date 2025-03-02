import json
import re
import boto3
# import pandas as pd

# Initialize the CloudWatch Logs client
log_group_name = 'hackattack'  
log_stream_name = 'hack_attack_standardised' 
client = boto3.client('logs', region_name='us-east-1') 

def get_logs(log_group_name, log_stream_name):
    '''
    This function is used to get logs from Cloudwatch
    '''
    response = client.get_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        startFromHead=True  # Set to False to get latest logs first
    )
    rejected_entries = []
    # Assuming the log messages are in the 'events' key of the response
    if 'events' in response:
          # List to store rejected entries
        for event in response['events']:
            message = event['message']

            # Check if the message is empty
            if not message:
                print("Empty message, skipping...")
                continue
            
            # Replace => with :
            message = message.replace("=>", ":")
            
            # Add quotes around keys for JSON compatibility
            message = re.sub(r'(\w+)\s*:', r'"\1":', message)  # Add quotes around keys
            
            # Attempt to parse the JSON
            try:
                # Extract the JSON part from the message
                json_part = message.split(" - ")[1]  # Get the JSON part after 'parsed_response - '
                data_list = json.loads(json_part)  # Parse the JSON

                # Iterate through the list of entries
                for entry in data_list[0]:  # Access the first element of the outer list
                    # Check if the status is "Rejected"
                    if entry['status'] == "Rejected":
                        rejected_entries.append(entry)

            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
                print(f"Message that caused the error: {message}")

        else:
            print("No rejected entries found.")

    else:
        print("No events found in the response.")

    return rejected_entries

def format_table(data):
    '''
    This function is used to format the table as required
    '''
    if not data:
        return "No data available."

    # Get the headers from the first dictionary
    headers = data[0].keys()
    
    # Create a list to hold the formatted rows
    rows = []
    
    # Add the header row
    header_row = " | ".join(f"{header}" for header in headers)
    rows.append(header_row)
    rows.append("-" * len(header_row))  # Add a separator line

    # Add each row of data
    for entry in data:
        row = " | ".join(f"{str(entry[header])}" for header in headers)
        rows.append(row)

    # Join all rows into a single string
    return "\n".join(rows)


def lambda_handler(event, context):
    '''
    The main function invoked by lamda_function
    '''
    rejected_entries = get_logs(log_group_name, log_stream_name)
    print(f'rejected_entries {rejected_entries}')
    # Convert the rejected_invoices to a DataFrame
    email_body = format_table(rejected_entries)
    
    # Prepare the email message
    subject = "Rejected Invoices Report"
    message = f"Rejected Invoices:\n\n{email_body}"
    
    # Send the email using SNS
    sns = boto3.client('sns')
    topic_arn = 'arn:aws:sns:us-east-1:823359494937:invoice_rejection_sns'  # Replace with your SNS topic ARN

    try:
        sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject
        )
        print("Email notification sent successfully.")
    except Exception as e:
        print(f"Error sending email notification: {e}")
    