import hashlib
import json
from time import time
from typing import Sequence
from urllib.parse import urlparse
import requests


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Create genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof: int, previous_hash=None) -> dict:
        """
        Create a new Block in the Blockchain
        :param proof: The proof given by the Proof of Work algo
        :param previous_hash: (Optional) Hash of the previous Block
        :return: New Block
        """
        block = {
            'index': len(self.chain)+1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: int) -> int:
        """
        Creates a new transaction to go into the next mined Block
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold new transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index']+1

    @staticmethod
    def hash(block) -> str:
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        :return: <str>
        """
        # Ordered Dict
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof: int):
        """
        Simple Proof of Work Algo:
            -Find a number p' such that hash(p*p') contains leading 4 zeroes, where p is the previous p'
            - p is the previous proof, p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contains 4 leading zeroes?
        :param last_proof: Previous Proof
        :param proof: Current Proof
        :return: True if correct, False if not.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_new_node(self, address: str) -> None:
        """
        Register a new Node
        """
        parse_url = urlparse(address)
        self.nodes.add(parse_url.netloc)

    def valid_chain(self, chain) -> bool:
        """
        Determine if a given blockchain is valid
        """
        last_block = chain[0]
        current_ind = 1

        while current_ind < len(chain):
            block = chain[current_ind]
            print(f"{last_block}\n{block}\n---------\n")
            # Check hash of the block
            if block['previous_hash'] != self.hash(last_block):
                return False
            # Check the proof of work
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_ind += 1

        return True

    def resolve_conflicts(self) -> bool:
        """
        Consensus algorithm; resolves coflicts by replacing a chain with the
        longest one in the network.
        :return: True if chain was replaced, otherwise False
        """
        neighbours = self.nodes
        new_chain = None

        default_max_len = len(self.chain)

        for node in neighbours:
            resp = requests.get(f'http://{node}/chain')

            if resp.status_code == 200:
                resp_body = resp.json()
                length = resp_body['length']
                chain = resp_body['chain']

                if length > default_max_len and self.valid_chain(chain):
                    default_max_len = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True

        return False
