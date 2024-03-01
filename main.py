from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import TransactionNotFound
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Web3 provider
provider_uri = os.getenv("WEB3_PROVIDER_URI")
provider = Web3.HTTPProvider(provider_uri)
web3 = Web3(provider)
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Set up contract addresses and ABI for TeaSwap project
teaswap_token_address = os.getenv("TEASWAP_TOKEN_ADDRESS")
dex_address = os.getenv("DEX_ADDRESS")
teaswap_token_abi = [...]  # Actual ABI of the TeaSwap token contract
dex_abi = [...]  # Actual ABI of the DEX contract for TeaSwap

# Set up wallet
private_key = os.getenv("PRIVATE_KEY")
wallet_address = web3.eth.account.from_key(private_key).address

# Initialize contract instances
teaswap_token_contract = web3.eth.contract(address=teaswap_token_address, abi=teaswap_token_abi)
dex_contract = web3.eth.contract(address=dex_address, abi=dex_abi)

def approve_token_spending(token_contract, spender_address, amount, wallet_address):
    try:
        tx_hash = token_contract.functions.approve(spender_address, amount).transact({'from': wallet_address})
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info("Approval transaction successful")
        return receipt
    except Exception as e:
        logger.error(f"Error approving token spending: {str(e)}")
        return None

def execute_swap(dex_contract, token_address, amount, wallet_address):
    try:
        tx_hash = dex_contract.functions.swap(token_address, amount).transact({'from': wallet_address})
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info("Swap transaction successful")
        return receipt
    except Exception as e:
        logger.error(f"Error executing swap: {str(e)}")
        return None

def get_gas_estimate(contract_function, *args, **kwargs):
    try:
        gas_estimate = contract_function(*args, **kwargs).estimateGas()
        logger.info(f"Gas estimate: {gas_estimate}")
        return gas_estimate
    except Exception as e:
        logger.error(f"Error estimating gas: {str(e)}")
        return None

def get_transaction_status(tx_hash):
    try:
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt.status
    except TransactionNotFound:
        return None

# Specify the amount of TeaSwap tokens to swap
amount_teaswap_tokens = web3.toWei(1, 'ether')  # Example: Swap 1 TeaSwap token for another token

# Approve DEX to spend TeaSwap tokens on behalf of the wallet
approve_receipt = approve_token_spending(teaswap_token_contract, dex_address, amount_teaswap_tokens, wallet_address)
if approve_receipt:
    gas_estimate_approve = get_gas_estimate(teaswap_token_contract.functions.approve, dex_address, amount_teaswap_tokens)
    if gas_estimate_approve:
        logger.info("Gas estimation successful")

        # Execute TeaSwap token swap
        swap_receipt = execute_swap(dex_contract, teaswap_token_address, amount_teaswap_tokens, wallet_address)
        if swap_receipt:
            gas_estimate_swap = get_gas_estimate(dex_contract.functions.swap, teaswap_token_address, amount_teaswap_tokens)
            if gas_estimate_swap:
                logger.info("Gas estimation successful")

                # Check transaction status
                swap_status = get_transaction_status(swap_receipt.transactionHash)
                if swap_status == 1:
                    logger.info("TeaSwap token swap completed successfully!")
                else:
                    logger.error("TeaSwap token swap failed")
            else:
                logger.error("Failed to estimate gas for swap transaction")
    else:
        logger.error("Failed to estimate gas for approval transaction")
else:
    logger.error("Failed to approve token spending")
