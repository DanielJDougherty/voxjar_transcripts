import voxjar
import json
import time
from dateutil.parser import parse
from datetime import datetime, timedelta
import re

# TODO: add retry logic for each request


def login(email, password, client, retry_count):
    document = """
      mutation($email:String!, $password:String!) {
        login(email:$email, password:$password)
      }
    """
    creds = {"email": email, "password": password}
    try:
      response = client.execute(document, variable_values=creds)
      return response.get("login")
    except Exception as e:
      print('failed to login: {}'.format(e))
      if retry_count<3:
        retry_count+=1
        print('pausing 2 secs')
        time.sleep(2)
        print('retrying')
        response = login(email, password, client, retry_count)
        return response
      else:
        return False
      

   

def get_transcripts( token, client, retry_count, offset):
  print('getting transcripts')

  # can only get 20 calls at a time. must use offset and incerment by 20
  # print(offset)
  document="""query($filter:CallFilterInput, $offset:Int) {
      calls(filter: $filter, offset:$offset) {
        id: identifier
        transcript{
          text
          timestamp
          confidence
          length
        }
       
      }
    }"""
  filters={"filter": {
            "timestamp": {
              "greaterThanOrEqualTo": "4d"
              # 'lessThanOrEqualTo': {'add': {'day': 1}, 'atStartOf': 'd'}, 'greaterThanOrEqualTo': {'subtract': {'day': 7}, 'atStartOf': 'd'}
            }
          },
          "offset":offset
        }
  try:
    response = client.execute(document, token=token, variable_values=filters)
    return response.get("calls",[])
  except Exception as e:
      print('failed to get transcript: {}'.format(e))
      if retry_count<3:
        retry_count+=1
        print('pausing 2 secs')
        time.sleep(2)
        print('retrying')
        response = get_transcripts(token, client, retry_count, offset)
        return response
      else:
        return False
  # print('transcript')



def main():
  # TODO: date filter, connect to database
  client = voxjar.Client(url='https://api.voxjar.com:9000')

  # Your credentials
  email="david@voxjar.com"
  password="sQmMbW8ZeXAZRcx"

  login_token = login(email, password, client, 0)
  transcripts ={}
  more= True
  offset=0

  while more:
    # print(offset)
    response = get_transcripts(login_token, client, 0, offset)
    offset += 20

    r = json.dumps(response)
    json_obj= json.loads(r)
    # print(len(json_obj))

    if len(json_obj) < 20:
      more = False
    elif len(json_obj)== 0:
      break
    
    for item in json_obj:
      transcripts[item['id']]={'id':str(item['id']), 'transcript':item['transcript']}
   
    # Comment following 2 lines to remove upper end limit
    if len(transcripts) >= 200:
      more = False

  
  with open('transcripts.json', 'w') as f:
      for record in transcripts:
        f.write(json.dumps(transcripts[record]).replace('\n',' ')+'\n')

  
  
if __name__ == "__main__":
    main()

 
