from flask import Blueprint, jsonify, request, url_for, abort
from web.models import db, Listing

from web.apis.auth import token_auth
from web.apis.errors import bad_request

from web.utils.save_image import uploader
from web.models import Listing

#from web.utils.categorylist import build_category_tree

listing_bp = Blueprint('listing_api', __name__)
mandatory_dt = ['images', 'title', 'price', 'contact', 'location', 'desc', 'cate']
mandatory_fields = ['images', 'title', 'price', 'contact', 'location', 'desc', 'cate']

from flask import request, jsonify, url_for
from web.extensions import db  # Import necessary extensions

@listing_bp.route('/listings1', methods=['POST'])
def create_listing1():

    if any(key not in data for key in mandatory_dt):
        return bad_request('Missing required info for this listing')

    saved_images = [uploader(x) for x in request.files.getlist('images') if x] or None
    
    data = request.get_json() or {}

    # Set default values for location and contact if not provided in the form
    locations = {'region': data.get('region'), 'city': data.get('city'), 'street': data.get('street'), 'zipcode': data.get('zipcode')}
    contacts = {'name': data.get('cont_name'), 'email': data.get('cont_email'), 'phone': data.get('cont_phone'), 'company': data.get('company')}

    """ data['locations'] = locations
    data['contacts'] = contacts
    data['images'] = saved_images """

    # Create a new Listing instance
    listing = Listing()

    # Update the JSON columns with the provided data
    listing.color = data.get('color')
    listing.size = data.get('size')
    listing.location = locations  # Assign the 'locations' dictionary
    listing.amenities = data.get('amenities')
    listing.contact = contacts  # Assign the 'contacts' dictionary
    listing.images = saved_images  # Assign the 'saved_images' list

    # Update any other columns you want here...
    # For example: listing.title = data.get('title')

    # Use the from_dict method to update the rest of the listing
    listing.from_dict(data, new_listing=True)

    # Add the listing to the database session and commit the transaction
    db.session.add(listing)
    db.session.commit()

    # Create a response with the listing's data
    response = jsonify(listing.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('listing_api.get_listing', id=listing.id)
    return response

@listing_bp.route('/listings', methods=['POST'])
def create_listing():
    # Check if the request contains JSON data
    #data = request.get_json()
    data = request.data()

    # Check if all mandatory fields are present
    if not all(field in data for field in mandatory_fields):
        return bad_request('Missing required information for this listing')

    # Create a new Listing instance and populate it with data
    listing = Listing()
    listing.from_dict(data, new_listing=True)

    # Add the listing to the database session and commit the transaction
    db.session.add(listing)
    db.session.commit()

    # Create a response with the listing's data
    response = jsonify(listing.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('listing_api.get_listing', id=listing.id)

    return response

@listing_bp.route('/listings/<int:id>', methods=['GET'])
@token_auth.login_required
def get_listing(id):
    return jsonify(Listing.query.get_or_404(id).to_dict())

@listing_bp.route('/listings', methods=['GET'])
#@token_auth.login_required
def get_listings():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Listing.to_collection_dict(Listing.query, page, per_page, 'listing_api.get_listings')
    return jsonify(data)

@listing_bp.route('/listings/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = Listing.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Listing.to_collection_dict(user.followers, page, per_page,
                                   'listing_api.get_followers', id=id)
    return jsonify(data)

@listing_bp.route('/listings/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user = Listing.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Listing.to_collection_dict(user.followed, page, per_page,
                                   'listing_api.get_followed', id=id)
    return jsonify(data)

@listing_bp.route('/listings/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_listing(id):
    if token_auth.current_user().id != id:
        abort(403)
    listing = Listing.query.get_or_404(id)
    data = request.get_json() or {}

    if any(key not in data for key in mandatory_dt):
        return bad_request('Missing required information for updating this listing')

    """ if 'images' in data and data['images'] != user.username and \
            Listing.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and \
            Listing.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address') """
    listing.from_dict(data, new_listing=False)
    db.session.commit()
    return jsonify(listing.to_dict())
