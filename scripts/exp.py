#!/use/bin/python
# import binascii
from brownie import accounts, network, config, DecentFl, Contract
import json
import requests
import uuid

def download_model_IPFS(cid):
    res = requests.get(f"https://ipfs.io/ipfs/{cid}")
    if res.status_code == 200:
        return res.content 
    else:
        print("Failed to downlaod model!")

file_path = "models/genesis.txt"
boundary = str(uuid.uuid4())
url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiI0NDgwMDczZC1kYmE3LTQ1NjAtYjA3MC04YjFhMTAxZGMwMWUiLCJlbWFpbCI6InNheWVkaGFpZGVyNDAxQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaW5fcG9saWN5Ijp7InJlZ2lvbnMiOlt7ImlkIjoiRlJBMSIsImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxfV0sInZlcnNpb24iOjF9LCJtZmFfZW5hYmxlZCI6ZmFsc2UsInN0YXR1cyI6IkFDVElWRSJ9LCJhdXRoZW50aWNhdGlvblR5cGUiOiJzY29wZWRLZXkiLCJzY29wZWRLZXlLZXkiOiI0YTkzMTY2NzZmNzk2ZDBhMmJjZCIsInNjb3BlZEtleVNlY3JldCI6IjdjMmMzNGJjMjg5MWI2NzMwOTZhMTMzMzM5NTlhYzE2ZDQyYmI3MzJhY2JmZDA3YTk0YjZmYTczMjBiZjg4MDgiLCJpYXQiOjE3MTU1MDI5MjB9.vsRidScGWkc2wHYpNut1GueOlAu6uIrxlaePPqfhkNk",
    'Content-Type': f"multipart/form-data; boundary={boundary}",
}

def upload_Model_IPFS(url, file_path, boundary, headers):
    with open(file_path, "rb") as f:
        file_content = f.read()
    payload = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"file.txt\"\r\n"
        "Content-Type: text/plain\r\n"
        "\r\n"
        f"{file_content.decode('utf-8')}\r\n"
        f"--{boundary}--\r\n"
    )
    response = requests.request("POST", url, data=payload, headers=headers)
    json_res = response.json()
    return json_res["IpfsHash"]


def get_account():
    if network.show_active() == "development":
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])

account = get_account()
decent_fl_contract = DecentFl.deploy({"from": account})

def deploy_test():
    print(decent_fl_contract.address)
    genesis_model = upload_Model_IPFS(url, "models/Genesis.txt", boundary, headers)
    genesis = decent_fl_contract.setGenesis(
        genesis_model,
        100,
        5,
        ['0x33A4622B82D4c04a53e170c638B944ce27cffce3',
        '0x0063046686E46Dc6F15918b61AE2B121458534a5',
        '0x21b42413bA931038f35e7A5224FaDb065d297Ba3',
        '0x46C0a5326E643E4f71D3149d50B48216e174Ae84']
    )
    print(genesis)
    
    print(decent_fl_contract.evaluator())
    print(decent_fl_contract.genesis())
    print(decent_fl_contract.getGlobalModel(1))
    add_model_update()

def add_model_update():
    current_round = decent_fl_contract.currentRound()
    current_trainers = decent_fl_contract.getCurTrainers(current_round)
    for trainer in current_trainers:
        if current_round == 1:
            genesis_model = download_model_IPFS(decent_fl_contract.genesis())
            decoded_genesis_string = genesis_model.decode("utf-8")
            print(genesis_model)
            update = decoded_genesis_string + "\n" + f"Client: {trainer}, Update Round {current_round}\n"
            ipfs_intermedite_file = open("models/intermediate.txt", "a")
            ipfs_intermedite_file.write("\n" + update)
            ipfs_intermedite_file.close()
            cid = upload_Model_IPFS(url, "models/intermediate.txt", boundary, headers)
            print(cid)
            res = decent_fl_contract.addModelUpdate(cid, current_round, {"from": trainer})
            print(res)
            
            
def evaluate_round():
    current_round = DecentFl.currentRound()
            
            
        

deploy_test()


# def main():
#     deploy_test()
    
# if __name__ == "__main__":
#     main()