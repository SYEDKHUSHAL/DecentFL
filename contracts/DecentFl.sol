// SPDX-License-Identifier: Unlicensed
pragma solidity ^0.8.6;


contract DecentFl{
    address public evaluator;
    string public genesis;
    uint256 internal genesisTimestamp;
    uint256 internal roundDuration;
    uint256 internal maxNumUpdates;
    uint256 internal timeSkipped;

    mapping(uint256 => string[]) internal updatesInRound;
    mapping(string => uint256) internal updateRound;
    mapping(address => string[]) internal updatesFromAddress;
    mapping(string => address) internal accountsFromUpdate;
    mapping(uint256 => address[]) internal curTrainers;
    mapping(uint256 => bool) internal evalFlag;
    mapping(uint256 => string) internal globalmodel;

    event Log(string _myString, uint256 round);

    modifier evaluatoronly() {
        require(tx.origin == evaluator, "Invalid Evaluator");
        _;
    }

    constructor() {
        evaluator = tx.origin;
    }

    function saveGlobalModel(string calldata _cid, uint256 _round) external evaluatoronly {
        globalmodel[_round] = _cid;
    }

    function getGlobalModel(uint256 _round) external view returns (string memory){
        return globalmodel[_round];
    }

    function completeEval(uint256 _round) external evaluatoronly {
        require(evalFlag[_round] == false, "eval already complete");
        evalFlag[_round] = true;
    }

    function getCurTrainers(uint256 _round) external view returns (address[] memory trainers){
        trainers = curTrainers[_round];
    }

    function isTrainer(address __address, uint256 _round) external view returns (bool trainCheckFlag){
        trainCheckFlag = false;
        for(uint i = 0; i < curTrainers[_round].length; i++){
            if(curTrainers[_round][i] == __address){
                trainCheckFlag = true;
            }else{
                continue;
            }
        }
        return trainCheckFlag;
    }

    function setCurTrainer(address[] calldata _addresses, uint256 _round) public evaluatoronly{
        for(uint i = 0; i < _addresses.length; i++){
            curTrainers[_round].push(_addresses[i]);
        }
    }

    function changeMaxNumUpdates(uint256 _maxNum) external evaluatoronly{
        maxNumUpdates = _maxNum;
    }

    function currentRound() public view returns (uint256 round){
        uint256 timeElapsed = timeSkipped + block.timestamp - genesisTimestamp;
        round = 1 + (timeElapsed / roundDuration);
    }

    //Check again "%"
    function secondsRemaining() public view returns (uint256 remaining){
        uint256 timeElapsed = timeSkipped + block.timestamp - genesisTimestamp;
        remaining = roundDuration - (timeElapsed % roundDuration);
    }

    function updates(uint256 _round) external view returns (string[] memory){
        return updatesInRound[_round];
    }

    function madeContribution(address _address, uint256 _round) public view returns (bool){
        for(uint256 i = 0; i < updatesFromAddress[_address].length; i++){
            string memory update = updatesFromAddress[_address][i];
            if(updateRound[update] == _round){
                return true;
            }
        }
        return false;
    }

    function setEvaluator(address _newEvaluator) external evaluatoronly{
        evaluator = _newEvaluator;
    }

    function setGenesis(
        string calldata _cid,
        uint256 _roundDuration,
        uint256 _maxNumUpdates,
        address[] calldata _accounts
    ) external evaluatoronly {
        require(bytes(genesis).length == 0, "Genesis Model already set");
        genesis = _cid;
        genesisTimestamp = block.timestamp;
        roundDuration = _roundDuration;
        maxNumUpdates = _maxNumUpdates;
        setCurTrainer(_accounts, 1);
    }

    function addModelUpdate(string memory _cid, uint256 _round) external{
        emit Log("curRound : ", currentRound());
        emit Log("Inserted Round : ", _round);
        require(_round > 0, "Cannot add update for genesis model");
        require(_round >= currentRound(), "Cannot add update for past round");
        require(_round <= currentRound(), "Cannot add update for future round");
        require(!madeContribution(tx.origin, _round), "Already added an update for this round");

        updatesInRound[_round].push(_cid);
        updatesFromAddress[tx.origin].push(_cid);
        accountsFromUpdate[_cid] = tx.origin;
        updateRound[_cid] = _round;
    }

    function skipRound(uint256 _round) external{
        if(
            maxNumUpdates > 0 && 
            updatesInRound[_round].length >= maxNumUpdates && 
            (evalFlag[_round] == true || _round == 1)
        ) {
            timeSkipped += secondsRemaining();
        }
    }

    function waitTrainers(uint256 _round) external view returns (bool){
        if(updatesInRound[_round].length >= maxNumUpdates){
            return true;
        }else{
            return false;
        }
    }

    function getMaxNum() public view returns (uint256){
        return maxNumUpdates;
    }

    function getAccountfromUpdate(string calldata _cid) external view returns(address){
        return  accountsFromUpdate[_cid];
    }

    
}