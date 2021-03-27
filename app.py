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


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """
    Register a new Node
    """
    body = request.get_json()
    nodes = body.get('nodes')
    if nodes is None:
        return "Error: Please provide a valid list of nodes", 400

    for node in nodes:
        blockchain.register_new_node(node)

    resp = {'message': "Successfully added new nodes.",
            'total_nodes': list(blockchain.nodes)}
    return jsonify(resp), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        resp = {'message': 'Our chain was replaced',
                'new_chain': blockchain.chain}
    else:
        resp = {'message': 'Our chain is authoritative',
                'new_chain': blockchain.chain}

    return jsonify(resp), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=6001)
