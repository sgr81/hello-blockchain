from flask import Flask, jsonify, request
from uuid import uuid4
from blockchain import Blockchain


# Node
app = Flask(__name__)

# Globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    try:
        sender = values['sender']
        recipient = values['recipient']
        amount = values['amount']
    except:
        return 'Invalid Request', 400

    index = blockchain.new_transaction(sender, recipient, amount)

    response = {'message': f'Transaction added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Reward for finding the proof
    # The sender is '0' to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        "message": "New Block Forged",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=6000)
