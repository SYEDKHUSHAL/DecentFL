Initialize an empty brownie project 
add a .env file. I will provide the keys for it later 

make sure your brownie-config.yaml filr contains the following content 

solc:
    version: 0.8.22
    evm_version: null
    optimize: true
    runs: 200
    minify_source: false
    remappings:
          - "@openzeppelin=OpenZeppelin/openzeppelin-contracts@3.0.0"
dotenvL: .env
wallets:
  from_key: ${PRIVATE_KEY}
