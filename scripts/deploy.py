# !/use/bin/python
from brownie import accounts, network, config, DecentFl, Contract
import requests
import uuid
import os
import glob
from dotenv import load_dotenv


def get_account():
    if network.show_active() == "development":
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])

account = get_account()
decent_fl_contract = DecentFl.deploy({"from": account})

def print_all_accounts():
    for x in accounts:
        print(x)



load_dotenv()
PINATA_AUTH = os.getenv('PINATA_AUTH')
boundary = str(uuid.uuid4())
url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
headers = {
    "Authorization": PINATA_AUTH,
    'Content-Type': f"multipart/form-data; boundary={boundary}",
}


def download_model_IPFS(cid):
    res = requests.get(f"https://ipfs.io/ipfs/{cid}")
    if res.status_code == 200:
        return res.content 
    else:
        print("Failed to downlaod model!")
    

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

def download_updates_from_round(round):
    updates = decent_fl_contract.updates(round)
    content_from_updates = []
    for cid in updates:
        content_from_updates.append(download_model_IPFS(cid))
    return content_from_updates
      
        
def aggregate(content_from_updates):
    aggregated_model = ""
    for update in content_from_updates:
        aggregated_model += f"\n{update.decode("utf-8")}"
    return aggregated_model


def aggregate_final_model(content_from_updates):
    aggregated_model = ""
    for update in content_from_updates:
        aggregated_model += f"\n{update}"
    return aggregated_model


def upload_global_model(file_path, round):
    cid = upload_Model_IPFS(url, file_path, boundary, headers)
    evaluator = accounts[0]
    round = decent_fl_contract.currentRound()
    return decent_fl_contract.saveGlobalModel( cid, round, {"from": evaluator})
    
    
def print_report(num_clients, num_rounds, round_duration, transactions_sent, gas_used, num_contributions):
    report = f"""
-------------------------------------------------------------------------------------------------------------------
    Decent FL process Completed for task with:
    Clients: {num_clients}
    Num Clients: {len(num_clients)}
    Num Contributions: {num_contributions}
    Num Rounds: {num_rounds}
    Round Duration: {round_duration}
    Transactions Sent: {transactions_sent}
    Gas Used: {gas_used}
    Final Model Stored in: models/final/Final Model
-------------------------------------------------------------------------------------------------------------------
    """
    print(report)
    
def clean_models_dir():
    files_array = [glob.glob('models/local/*'), glob.glob('models/global/*'), glob.glob('models/final/*')]
    for item in files_array:
        for file in item:
            os.remove(file)
    

def start_decent_fl():
    clean_models_dir()
    transactions_sent = 2
    for round in range(2):
        current_round = decent_fl_contract.currentRound()
        if current_round > 1:
            decent_fl_contract.setCurTrainer(['0x33A4622B82D4c04a53e170c638B944ce27cffce3',
                                                '0x0063046686E46Dc6F15918b61AE2B121458534a5']
                                             , current_round)
            transactions_sent += 1
        current_trainers = decent_fl_contract.getCurTrainers(current_round)

        for trainer in current_trainers:
            if current_round == 1:
                genesis_model = download_model_IPFS(decent_fl_contract.genesis())
                decoded_genesis_string = genesis_model.decode("utf-8")
                update = decoded_genesis_string + "\n" + f"Client: {trainer}, Update Round {current_round}"
                local_model_file = open(f"models/local/Round:{current_round} Client: {trainer}.txt", "a")
                local_model_file.write("\n" + update)
                local_model_file.close()
                cid = upload_Model_IPFS(url, f"models/local/Round:{current_round} Client: {trainer}.txt", boundary, headers)
                print(cid)
                res = decent_fl_contract.addModelUpdate(cid, current_round, {"from": trainer})
                transactions_sent += 1
                print(res)
            else:
                gbl_model_cid = decent_fl_contract.getGlobalModel(current_round - 1)
                gbl_mdl = download_model_IPFS(gbl_model_cid)
                decoded_gbl_mdl_string = gbl_mdl.decode("utf-8")
                update = decoded_gbl_mdl_string + "\n" + f"Client: {trainer}, Update Round {current_round}"
                local_model_file = open(f"models/local/Round:{current_round} Client: {trainer}.txt", "a")
                local_model_file.write("\n" + update)
                local_model_file.close()
                cid = upload_Model_IPFS(url, f"models/local/Round:{current_round} Client: {trainer}.txt", boundary, headers)
                print(cid)
                res = decent_fl_contract.addModelUpdate(cid, current_round, {"from": trainer})
                transactions_sent += 1
                print(res)

        updates_list = download_updates_from_round(current_round)
        global_model = aggregate(updates_list)
        global_model_file = open(f"models/global/Global Model Round:{current_round}.txt", "a")
        global_model_file.write(global_model)
        global_model_file.close()
        print(upload_global_model(f"models/global/Global Model Round:{current_round}.txt", current_round))
        transactions_sent += 1
        decent_fl_contract.completeEval(current_round, {"from": accounts[0]})
        transactions_sent += 1
        print(f"Evaluated Round : {current_round}")
        decent_fl_contract.skipRound(current_round)
        transactions_sent += 1

    global_models = []
    for i in range(2):
        path = f"models/global/Global Model Round:{i + 1}.txt"
        file = open(path, "r")
        content = file.read()
        global_models.append(content)
        file.close()
       
    final_model = aggregate_final_model(global_models)
    path = "models/final/Final Model.txt"
    file = open(path, "a")
    file.write(final_model)
    file.close()
    num_clients = decent_fl_contract.getCurTrainers(1)
    print_report(num_clients, 2, 100, transactions_sent, "##", "##")


def deploy_decent_fl():
    print(decent_fl_contract.address)
    genesis_model = upload_Model_IPFS(url, "genesis/Genesis.txt", boundary, headers)
    genesis = decent_fl_contract.setGenesis(
        genesis_model,
        100,
        2,
        ['0x33A4622B82D4c04a53e170c638B944ce27cffce3',
        '0x0063046686E46Dc6F15918b61AE2B121458534a5']
    )
        # '0x21b42413bA931038f35e7A5224FaDb065d297Ba3',
        # '0x46C0a5326E643E4f71D3149d50B48216e174Ae84']
    print(genesis)
    
    print(decent_fl_contract.evaluator())
    print(decent_fl_contract.genesis())
    print(decent_fl_contract.getGlobalModel(1))
    start_decent_fl()


def main():
    deploy_decent_fl()
    
if __name__ == "__main__":
    main()