import json
import re
import boto3
import botocore.config
from datetime import datetime
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
    all_entries = []
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
                    all_entries.append(entry)

            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
                print(f"Message that caused the error: {message}")

    else:
        print("No events found in the response.")

    return all_entries

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

def genai_logs_message(question, report):
    '''
    This functions returns the prompt used by genai model
    '''
    messages = []
    # User message providing the context
    page_message = {
        "role": "user",
        "content": [
                           {
                "type": "text",
                "text": f''' Report of rejected invoices: {report}'''
                           },
                           {
                "type":"text",
                "text": f'''Question {question}''',
                           }
        ],
    }
    messages.append(page_message)
    # System message for giving instructions to the genai model
    system_message = {
        "role": "assistant",
        "content": f"""You are an AI assistant that can answer questions based on the provided data"""
    }
    messages.append(system_message)

    return messages

def details_generate_using_bedrock(question):
    '''
    This function is used to invoke the genai model and return the appropriate response
    '''
    all_entries = get_logs(log_group_name, log_stream_name)
    email_body = format_table(all_entries)
    messages = genai_logs_message(question, email_body)

    # formatting the input for genai model
    body = {
    "messages": messages,  # List of messages
    "max_tokens": 1000,      # Optional: Adjust max tokens as needed
    "anthropic_version": "bedrock-2023-05-31",  # Optional: Adjust version or remove based on your model
    }

    # invoking the genai model 
    try:
        print(f'invoking bedrock with body')

        bedrock=boto3.client("bedrock-runtime",region_name="us-east-1",
                             config=botocore.config.Config(read_timeout=300,retries={'max_attempts':3}))
        
        response=bedrock.invoke_model(body=json.dumps(body),modelId="anthropic.claude-3-5-sonnet-20240620-v1:0")
        response_content=response.get('body').read()
        response_data=json.loads(response_content)
        final_details_dict = {}
        if len(response_data['content']):
            details = response_data['content'][0]['text']
            details = details.split('\n')
            details = [x for x in details if len(details)>0]
            for ind, elem in enumerate(details):
                final_details_dict[ind]=elem
        
        return final_details_dict
    except Exception as e:
        print(f"Error generating the details:{e}")
        return {'error':f'Error generating the details:{e}'}


def lambda_handler(event, context):
    '''
    The main function invoked by lamda_function
    '''
    event=json.loads(event['body'])
    # questions asked by the user
    question=event['question']
    print(f'Question \n {question}')
    answer = details_generate_using_bedrock(question)
    # the answer given by the genai model
    print(f'Answer \n {answer}')
    return{
        'statusCode':200,
        'body':json.dumps(answer)
    }


    




    