import json
from urllib import parse
import boto3
import string
import random
import time
client = boto3.client('dynamodb')
dynamoResource = boto3.resource('dynamodb')
table = dynamoResource.Table("InstanceDetailsDB")
# Function to execute SSM command on nginx 
def execute_ssm_commands(instance_id, commands):
    ssm_client = boto3.client('ssm')

    response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': commands}
    )

    command_id = response['Command']['CommandId']
    
    # You may want to implement logic to wait for the command to complete or check its status

    return command_id
    
def lambda_handler(event, context):
    ######################################################
    # Generate Random Character String
    length = 9
    characterList = ""
    characterList += string.ascii_letters
    passwordArray = []
    for i in range(length):
    
    	# Picking a random character from our 
    	# character list
    	randomchar = random.choice(characterList)
    
    	# appending a random character to password
    	passwordArray.append(randomchar)
    
    randomLocation = "".join(passwordArray)
    
    #Empty Array to append and retrieve UN-LINKED instances
    unoccInst = []
    ########################################################

    unoccInstID = []
    
# Master instance ID
    #instance_id = 'i-0c43202564b35d48f'
    instance_id = 'i-0e580810d34d58d98'
     

#Fetch Un-linked IP from DynamoDB

    data = client.scan(
    TableName='InstanceDetailsDB'
    )
    for x in data['Items']:
        
        print(x)
        # Check if instance available
        if x['Linked']['BOOL'] == False:
            unoccInst.append(x['ipAddress']['S'])
            unoccInstID.append(x['instance_id']['S'])

    fetchedIP = unoccInst[0]	
    response3 = table.update_item(
        Key={"instance_id": unoccInstID[0]},
        UpdateExpression="set #name = :n",
        ExpressionAttributeNames={
            "#name": "randomString",
        },
        ExpressionAttributeValues={
            ":n": randomLocation,
        },
        ReturnValues="UPDATED_NEW",
    )
    
# Run Sed command in Nginx to update IP in config file
  #test sed command
    sed_command = "sudo sed -i '/#anchor-for-ssm/i\ \ \ location /"+randomLocation+"/ {\\n\\ \ \ \ \ rewrite ^/"+randomLocation+"(\\/.*?)$ $1 break; \\n\\ \ \ \ \ proxy_pass http:\\/\\/"+fetchedIP+"\\/;\\n\\ \ \ }' /etc/nginx/sites-available/verchool.online"
  #main sed command  
    #sed_command = "sudo sed -i '/#anchor-for-ssm/i\ \ \ location /"+randomLocation+"/ {\\n\\ \ \ \ \ rewrite ^/"+randomLocation+"(\\/.*?)$ $1 break; \\n\\ \ \ \ \ proxy_pass http:\\/\\/"+fetchedIP+"\\/;\\n\\ \ \ \ \ include \/etc\/nginx\/sites-available\/proxy_settings;\\n\\ \ \ }' /etc/nginx/sites-available/verchool.online"
    
    reload_command = "sudo systemctl reload nginx"
    
    # reload_command_2 = "sudo systemctl reload nginx"
    
    # List of commands to be executed sequentially
    commands = [sed_command, reload_command]
    
    command_id = execute_ssm_commands(instance_id, commands)
    
#     # Build our response object as a python dict object
       
        # time.sleep(3)
        # print("delayed by 3 sec")

    
    # response5 = dict()
    # response5["statusCode"] = 302
    # response5["body"]= json.dumps(dict())

    # response5["headers"] = {"Location": f"https://verchool.online/{randomLocation}/?hoveringMouse=true"}
    #response5["headers"] = {"Location": "http://google.com"}
    
    
    #Build the API Gateway response - NO REDIRECTION
    response5 = dict()
    response5["statusCode"] = 200  #not redirecting
    response5["body"] = json.dumps({"newURL": f"https://verchool.online/{randomLocation}/?hoveringMouse=true"})
    response5["headers"] = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://verchool.online",
    }
    
    print(f"Respnse being returned to API Gateway, then to the user: {response5}")
    
    response3 = table.update_item(
    Key={"instance_id": unoccInstID[0]},
    UpdateExpression="set #name = :n",
    ExpressionAttributeNames={
        "#name": "Occupied",
    },
    ExpressionAttributeValues={
        ":n": True,
    },
    ReturnValues="UPDATED_NEW",
    )
    response3 = table.update_item(
    Key={"instance_id": unoccInstID[0]},
    UpdateExpression="set #name = :n",
    ExpressionAttributeNames={
        "#name": "Linked",
    },
    ExpressionAttributeValues={
        ":n": True,
    },
    ReturnValues="UPDATED_NEW",
    )
    # commands = [reload_command]
    # execute_ssm_commands(instance_id, commands)
    return response5 
