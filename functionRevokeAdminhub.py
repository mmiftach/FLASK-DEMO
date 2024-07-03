# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
import json
import os
from dotenv import load_dotenv
import csv

load_dotenv()

def revokeJira(userId):
  token = os.getenv("CLOUDSESSIONTOKEN")
  acountId = userId
  #old url = "https://admin.atlassian.com/gateway/api/adminhub/um/site/d671a7c1-0502-419d-b721-1028332bc10a/users/"+acountId+"/deactivate"
  url = "https://admin.atlassian.com/gateway/api/adminhub/um/org/9b02d1eb-a23d-4222-9b04-444ba42b9d0a/users/"+acountId+"/deactivate"

  headers = {
    "Content-Type": "application/json",
    'Cookie': token
  }

  payload = json.dumps( {
    "message": "On 6-month suspension"
  } )

  response = requests.post(url, headers={'Cookie': "cloud.session.token="+token})
  return response.status_code

def convertCSVtoList(csvFile):
    with open(csvFile, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        list = []
        for row in reader:
            list.append(row)
    return list

def revokeListJira(data):
  listRevokeUser = convertCSVtoList(data)  # Convert the DataFrame to a list
  revokedUsers = []  # Step 1: Initialize an empty list to store revoked user IDs
  for index, revokeUser in enumerate(listRevokeUser):
      if index == 0:
          continue  # Skip the first iteration
      print(revokeJira(revokeUser[0]))  # Step 2: Print the response from the revokeJira function
      revokedUsers.append(revokeUser)  # Step 2: Append the user ID to the list
  return revokedUsers  # Step 3: Return the list of revoked user IDs