import datetime
import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = str(os.getenv("BOT_TOKEN"))

# 465989596
#    902545686
admins = [
    465989596,
]

def get_access_list():
    with open('access.txt', 'r') as file:
        lines = file.read().splitlines()
        access = []
        for line in lines:
            if line:
                try:
                    access.append(int(line))
                except:
                    pass
    return access

def remove_from_access_list(user_id):
    with open('access.txt', 'r') as infile:
        newlist= [i for i in infile.read().split() if i!=user_id]
        
    with open('access.txt','w') as outfile:
        outfile.write("\n".join(newlist))