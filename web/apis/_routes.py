import json

from flask import request, jsonify, Blueprint

apis = Blueprint('apis', __name__)

listings = [
 { 'id': 1, 'name': 'Ashley' },
 { 'id': 2, 'name': 'Kate' },
 { 'id': 3, 'name': 'Joe' }
]

nextListingId = 4

@apis.route('/listings', methods=['GET'])
def get_listings():
    return jsonify(listings)

@apis.route('/listings/<int:id>', methods=['GET'])
def get_listing_by_id(id: int):
    listing = get_listing(id)
    if listing is None:
        return jsonify({ 'error': 'Listing does not exist'}), 404
    return jsonify(listing)

def get_listing(id):
    return next((ls for ls in listings if ls['id'] == id), None)

def listing_is_valid(listing):
    for key in listing.keys():
        if key != 'name':
            return False
        return True

@apis.route('/listings', methods=['POST'])
def create_listing():
    global nextListingId
    listing = json.loads(request.data)
    if not listing_is_valid(listing):
        return jsonify({ 'error': 'Invalid listing properties.' }), 400

    listing['id'] = nextListingId
    nextListingId += 1
    listings.append(listing)

    return '', 201, { 'url': f'/listings/{listing["id"]}' }

@apis.route('/listings/<int:id>', methods=['PUT'])
def update_listing(id: int):
    listing = get_listing(id)
    if listing is None:
        return jsonify({ 'error': 'Listing does not exist.' }), 404

    updated_listing = json.loads(request.data)
    if not listing_is_valid(updated_listing):
        return jsonify({ 'error': 'Invalid listing properties.' }), 400

    listing.update(updated_listing)

    return jsonify(listing)

@apis.route('/listings/<int:id>', methods=['DELETE'])
def delete_listing(id: int):
    global listings
    listing = get_listing(id)
    if listing is None:
        return jsonify({ 'error': 'Listing does not exist.' }), 404

    listings = [ls for ls in listings if ls['id'] != id]
    return jsonify(listing), 200

