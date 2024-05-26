import time, jwt, os
from datetime import datetime
from flask_login import UserMixin
from web.extensions import db

"""
from flask import current_app, g
from web.extensions import db, s_manager, oauth, bcrypt, mail
@s_manager.user_loader
def load_user(uid):
    # Load the user from the session or wherever you store user information
    # and store it in the "g" object for the current request
    g.user = User.query.get(int(uid))  # Replace with your user loading logic
    return g.user
#this-will-allow-support-for-multiple-category-for-a-product """

tag_item = db.Table(
    'tag_item', db.Model.metadata,
    db.Column('item_id', db.Integer, db.ForeignKey('item.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)
wishlist_item = db.Table(
    'wishlist_item',
    db.Column('wishlist_id', db.Integer, db.ForeignKey('wishlist.id')),
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'))
)
promotion_item = db.Table(
    'promotion_item',
    db.Column('promotion_id', db.Integer, db.ForeignKey('promotion.id')),
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'))
)
user_permissions = db.Table(
    'user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True),
    keep_existing=True
)
usr_role = db.Table(
    'usr_role',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    keep_existing=True
)
# Create a table to represent the many-to-many relationship between roles and permissions
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)
class Brand(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    kind = db.Column(db.String(100), unique=True, nullable=False, default='Sales')
    name = db.Column(db.String(100), unique=True, nullable=False, default='ecommerce')
    email = db.Column(db.String(100), unique=True, index=True, nullable=False, default='sales@internet.com')
    phone = db.Column(db.String(20), unique=True)
    photo = db.Column(db.String(1000))
    title = db.Column(db.String(50))
    logo = db.Column(db.Text())  # ['male','female','other']
    city = db.Column(db.String(50))
    lang = db.Column(db.String(100))
    us = db.Column(db.String(1000))
    owner = db.Column(db.String(500))
    hype = db.Column(db.String(10000))  #slogan
    ratings = db.Column(db.Integer)
    reviews = db.Column(db.Integer)
    bank = db.Column(db.String(100), default='fcmb')
    acct = db.Column(db.Integer, default=5913408010)
    status = db.Column(db.Boolean(), default=True)
    verified = db.Column(db.Boolean(), default=False)
    
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    name = db.Column(db.String(100), index=True)
    username = db.Column(db.String(100), index=True, nullable=False, unique=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, index=True)  #str type recommended bcos they're not meant for calculations
    password = db.Column(db.String(500), index=True, nullable=False)
    image = db.Column(db.String(1000))
    gender = db.Column(db.String(50))  # ['male','female','other']
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    about = db.Column(db.String(5000))
    reviews = db.Column(db.Integer)
    acct_no = db.Column(db.String(50))
    bank = db.Column(db.String(50))
    socials = db.Column(db.JSON, default={}) # socials: { 'fb': '@chrisjsm', 'insta': '@chris', 'twit': '@chris','linkedin': '', 'whats':'@techa' }
    src = db.Column(db.String(50))
    cate = db.Column(db.String(50))
    online = db.Column(db.Boolean(), default=False)  # 1-online, 0-offline
    status = db.Column(db.Boolean(), default=False)  # [ active(1), not active(0)]
    verified = db.Column(db.Boolean(), default=False)  # verified or not
    ip = db.Column(db.String(50))
    is_vendor = db.Column(db.Boolean, default=False, nullable=False)
    # Define relationships for both buying and selling
    #vendors = db.relationship('Vendor', backref='user', lazy=True)
    items = db.relationship('Item', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy=True)
    addresses = db.relationship('Address', backref='user', lazy=True)
    shipping_addresses = db.relationship('ShippingAddress', backref='user', lazy=True)
    notifications = db.relationship("Notification", backref="users", lazy=True) 
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    wishlists = db.relationship('Wishlist', backref='user', lazy='dynamic')
    favorites = db.relationship('FavoriteProduct', backref='user', lazy='dynamic')
    promotions = db.relationship('Promotion', backref='user', lazy='dynamic')
    analytics = db.relationship('AnalyticsEvent', backref='user', lazy='dynamic')
    roles = db.relationship('Role', secondary=usr_role, backref='user_roles', lazy='dynamic')

    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted
    
    def is_admin(self):
        return any(role.type == 'admin' for role in self.role)
    
    def permit(self):
        return [ r.type for r in self.role ]

    def generate_token(self, exp=600, type='reset'):
        return jwt.encode({'uid': self.id, 'exp': time.time() + exp, 'type': type }, os.environ.get('secret_key'), algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        try:
            uid = jwt.decode(token, os.environ.get('secret_key'), algorithms=['HS256'])['uid']
            user = User.query.get(uid)
            type = jwt.decode(token, os.environ.get('secret_key'), algorithms=['HS256'])['type']
        except:
            return
        return user, type

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.photo}')"

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    desc = db.Column(db.Text, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, index=True)  #str type recommended bcos they're not meant for calculations
    password = db.Column(db.String(500), index=True, nullable=False)
    image = db.Column(db.String(1000))
    gender = db.Column(db.String(50))  # ['male','female','other']
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    about = db.Column(db.String(5000))
    reviews = db.Column(db.Integer)
    acct_no = db.Column(db.String(50))
    bank = db.Column(db.String(50))
    socials = db.Column(db.JSON, default={}) # socials: { 'fb': '@chrisjsm', 'insta': '@chris', 'twit': '@chris','linkedin': '', 'whats':'@techa' }
    #items = db.relationship('Item', backref='vendor_info', lazy='dynamic')
    promotions = db.relationship('Promotion', backref='vendor', lazy=True)
    deleted = db.Column(db.Boolean(), default= 0)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True)
    message = db.Column(db.String(255))
    image = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    
    deleted = db.Column(db.Boolean(), default=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

#can be (admin/manager/supervisor) etc
class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    desc = db.Column(db.String(255))

#can be (read/write/edit/delete)
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    desc = db.Column(db.String(255))
    user = db.relationship('User', secondary=usr_role, backref='user_roles', lazy='dynamic') #FK linking role->user(many->many-rel)
    permissions = db.relationship('Permission', secondary=role_permissions, backref='roles', lazy='dynamic')

class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(1000), unique=True) #(stock keeping unit)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_qty = db.Column(db.Integer, nullable=False, default='1')
    desc = db.Column(db.Text)
    images = db.Column(db.JSON, nullable=False, default='blank.png')

    attributes = db.Column(db.JSON) #[ weight, size, condition, model, type, subtype, processor etc] 
    color = db.Column(db.JSON) #color:- {'red','wine', 'etc'},
    size = db.Column(db.JSON) #size:- {'s','m', 'l', 'xl', 'xxl'},

    # Add fields relevant to all listing types
    listing_type = db.Column(db.String(50), nullable=False)  # 'physical', 'digital', 'real_estate', 'local', etc.
    # Additional fields specific to different listing types
    property_type = db.Column(db.String(50))  # For real estate listings
    bedrooms = db.Column(db.Integer)          # For real estate listings
    bathrooms = db.Column(db.Integer)         # For real estate listings
    location = db.Column(db.String(255))     # For local listings
    job_type = db.Column(db.String(50))      # For job listings
    service_type = db.Column(db.String(50))  # For service listings

    tags = db.relationship('Tag', secondary=tag_item, back_populates='items', lazy='dynamic')
    promotions = db.relationship('Promotion', secondary=promotion_item, backref='promotion_item', lazy='dynamic')

    vendor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #vendor_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=False)
    #vendor = db.relationship('User', backref='user', lazy=True, primaryjoin='Item.vendor_id == User.id')

    cate_id = db.Column(db.Integer, db.ForeignKey('cate.id'))
    cate = db.relationship('Cate', backref='items', lazy=True, primaryjoin='Item.cate_id == Cate.id')

    reviews = db.relationship('Review', backref='item', lazy='dynamic')
    favorite = db.relationship('FavoriteProduct', backref='item', lazy='dynamic')

    instock = db.Column(db.Boolean(), default=True) #[list as in instock, for non-single items,]

    ip = db.Column(db.String(50))
    is_active = db.Column(db.Boolean(), default=True) #[sold, active,]
    deleted = db.Column(db.Boolean(), default=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def exists(item):
        return Item.query.filter(Item.id==item).first() is not None

class Cate(db.Model):  #levels-> (super1->main2->sub3->mini4)
    __tablename__ = 'cate'
    id = db.Column(db.Integer, primary_key=True)
    lev = db.Column(db.Integer, default=0)
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(100))
    photo = db.Column(db.String(50))
    #dept = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('cate.id'))
    #children = db.relationship('Cate', backref=db.backref('parent', remote_side=[id]))
    children = db.relationship('Cate', backref='parent', remote_side=[id] )

    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    items = db.relationship('Item', secondary=tag_item, back_populates='tags', lazy='dynamic')

#can be comments/likes/dislikes/reviews/views
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    
    replies = db.relationship('Reply', backref='review', lazy='dynamic')
    likes = db.relationship('Like', backref='review', lazy='dynamic')
    dislikes = db.relationship('Dislike', backref='review', lazy='dynamic')
    comments = db.relationship('Comment', backref='review', lazy='dynamic')

    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)

class Dislike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PaymentMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    secretkey = db.Column(db.String(255))
    # Add fields relevant to each payment method (e.g., API keys, configurations)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Pending, Success, Failure, etc.
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    """ 
    txn_ref = db.Column(db.String(100)) #['dollar, naira etc]
    txn_amt = db.Column(db.Integer())
    txn_desc = db.Column(db.String(100)) 
    txn_status = db.Column(db.String(100), default='pending') #['pending','successful', 'cancelled', 'reversed']
    currency_code = db.Column(db.String(100)) #['dollar, naira, cedis etc]
    provider = db.Column(db.String(100)) #['paypal','stripe', 'visa', 'mastercard', paystack']
    """

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)

class TopUpTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shipping_address = db.relationship('ShippingAddress', backref='order', lazy='dynamic')
    order_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    item_qty = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)

class ShippingAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)

class Promotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    max_discount_amount = db.Column(db.Float)
    expiration_date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    items = db.relationship('Item', secondary=promotion_item, backref='promotion_item', lazy='dynamic')

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    items = db.relationship('Item', secondary='wishlist_item', backref='wishlists', lazy='dynamic')

class FavoriteProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

class AnalyticsEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    event_type = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data = db.Column(db.JSON, nullable=True)

""" 
new_event = AnalyticsEvent(
    user_id=current_user.id if current_user.is_authenticated else None,
    event_type='item_view',
    data={'item_id': item.id, 'item_name': item.name}
)
db.session.add(new_event)
db.session.commit()
 
"""
# ********************** ########
""" 
# Find products with a specific tag
tagged_products = Tag.query.filter_by(name='electronics').first().products

# Find products with multiple tags
filtered_products = Product.query.filter(Product.tags.any(Tag.name.in_(['electronics', 'gadgets']))).all()

 """

class Expenses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    cost = db.Column(db.Integer)
    dept = db.Column(db.String(80), nullable=False, default='k') #[k=kitchen, c=cocktail, b=bar]
    desc = db.Column(db.String(100)) #desc
    
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
   