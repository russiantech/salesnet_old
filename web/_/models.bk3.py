import time, jwt, os
from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from web.utils.search import  SearchableMixin

cate_listing = db.Table(
    'cate_listing',
    db.Model.metadata,
    db.Column('cate_id', db.Integer, db.ForeignKey('cate.id')),
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id'))
)
tag_listing = db.Table(
    'tag_listing', db.Model.metadata,
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)
wishlist_listing = db.Table(
    'wishlist_listing',
    db.Column('wishlist_id', db.Integer, db.ForeignKey('wishlist.id')),
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id'))
)
promotion_listing = db.Table(
    'promotion_listing',
    db.Column('promotion_id', db.Integer, db.ForeignKey('promotion.id')),
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id'))
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

class User(db.Model, SearchableMixin, UserMixin):
    __searchable__ = ['name', 'username', 'email', 'phone', 'about']
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
    acct_no = db.Column(db.String(50))
    bank = db.Column(db.String(50))
    socials = db.Column(db.JSON, default=None) # socials: { 'fb': '@chrisjsm', 'insta': '@chris', 'twit': '@chris','linkedin': '', 'whats':'@techa' }
    src = db.Column(db.String(50))
    cate = db.Column(db.String(50))
    ip = db.Column(db.String(50))
    online = db.Column(db.Boolean(), default=False)  # 1-online, 0-offline
    status = db.Column(db.Boolean(), default=True)  # [ active(1), not active(0)]
    verified = db.Column(db.Boolean(), default=False)  # verified or not
    is_vendor = db.Column(db.Boolean, default=False, nullable=False)
    # Define relationships for both buying and selling
    #vendors = db.relationship('Vendor', backref='user', lazy=True)
    pages = db.relationship('Pages', back_populates='user')
    #listing = db.relationship('Listing', backref='user', lazy='dynamic')
    listing = db.relationship('Listing', back_populates='user',  lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy=True)
    addresses = db.relationship('Address', backref='user', lazy=True)
    shipping_addresses = db.relationship('ShippingAddress', backref='user', lazy=True)
    notifications = db.relationship("Notification", backref="users", lazy=True) 
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    wishlist = db.relationship('Wishlist', backref='user', lazy='dynamic')
    favorites = db.relationship('FavoriteProduct', backref='user', lazy='dynamic')
    promotions = db.relationship('Promotion', backref='user', lazy='dynamic')
    analytics = db.relationship('AnalyticsEvent', backref='user', lazy='dynamic')
    roles = db.relationship('Role', secondary=usr_role, back_populates='user', lazy='dynamic')

    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted
    
    def is_admin(self):
        return any(role.type == 'admin' for role in self.roles)
    
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

""" class Vendor(db.Model):
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
    #items = db.relationship('Listing', backref='vendor_info', lazy='dynamic')
    promotions = db.relationship('Promotion', backref='vendor', lazy=True)
    deleted = db.Column(db.Boolean(), default= 0)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
     """
class Pages(db.Model, SearchableMixin):
    __tablename__ = 'pages'
    __searchable__ = ['name', 'username', 'email', 'phone', 'about']
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
    socials = db.Column(db.JSON, default=None) # socials: { 'fb': '@chrisjsm', 'insta': '@chris', 'twit': '@chris','linkedin': '', 'whats':'@techa' }
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='pages')

    listing = db.relationship('Listing', back_populates='pages', lazy='dynamic')
    promotions = db.relationship('Promotion', backref='page', lazy=True)
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
    user = db.relationship('User', secondary=usr_role, back_populates='roles', lazy='dynamic') #FK linking role->user(many->many-rel)
    permissions = db.relationship('Permission', secondary=role_permissions, backref='roles', lazy='dynamic')

class Listing(db.Model, SearchableMixin):
    __tablename__ = 'listing'
    __searchable__ = ['title','price', 'desc', 'images', 'phone', 'about', 'required_skills','required_skills','make','amenities','listing_brand','address','listing_type']
    id = db.Column(db.Integer, primary_key=True)
    #page_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cate_id = db.Column(db.Integer, db.ForeignKey('cate.id'), nullable=False)
    title = db.Column(db.String(80), nullable=False)
    images = db.Column(db.JSON, nullable=False)
    currency = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    pay_interval = db.Column(db.String(50)) #like monthly for listing like property, like maybe commission-based for listing like jobs/services
    desc = db.Column(db.Text)
    negotiable = db.Column(db.Boolean(), default=False)
    listing_type = db.Column(db.String(50), nullable=False, default='physical') 
    listing_brand = db.Column(db.String(50))  
    address = db.Column(db.String(50)) 
    condition =  db.Column(db.String(50)) #(New, Used like new, Used good, Used fair)
    ip = db.Column(db.String(50))
    meet_up = db.Column(db.JSON)
    availability  = db.Column(db.String(50)) #instock,single item,avaialable,//Will be updated to 'sold' if initially a single item and it's sold,
    company = db.Column(db.String(50))

    #Listings
    sku = db.Column(db.String(1000), unique=True) #(stock keeping unit)
    stock_qty = db.Column(db.Integer, default='1')
    discount = db.Column(db.Integer)
    
    color = db.Column(db.JSON, default=None) #color:- {'red','wine', 'etc'},
    size = db.Column(db.JSON, default=None) #size:- {'s','m', 'l', 'xl', 'xxl'},

    # Property/Real Estate
    property_size  = db.Column(db.Integer)      
    bedrooms = db.Column(db.Integer)      
    bathrooms = db.Column(db.Integer)     
    property_for = db.Column(db.String(50)) #[for (rent/for sale)]
    amenities = db.Column(db.JSON)
    date_available = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    #Vehicle(s)-listing
    fuel_type = db.Column(db.String(50)) #[diesel, electric,gasoline,flex,hybrid,petrol,plug-in hybrid, other]
    make = db.Column(db.String(50))      
    model = db.Column(db.String(50))     
    year = db.Column(db.String(50))  

    #Jobs-listing
    job_level = db.Column(db.String(50)) # For job listings[senior, middle, leadership, junior]
    min_exp = db.Column(db.String(50), default='1')    #minimum experience
    min_qualify  = db.Column(db.String(50))       
    pay_range  = db.Column(db.Integer, default=None)       
    responsibilities  = db.Column(db.String(50))       
    required_skills   = db.Column(db.String(50))       
    job_setup   = db.Column(db.String(50))  #remote,office,hybrid 

    location = db.Column(db.JSON) #location:- {'region':'USA', 'city':'london', 'street':'beach-house, 27 california', 'zipcode':'1099990'},
    contact = db.Column(db.JSON) #contact:- see location column for sample using(name:name,emal:email,phone:phone,etc)
    
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    pages = db.relationship('Pages', back_populates='listing')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='listing', primaryjoin='User.id == Listing.user_id')
    
    wishlist = db.relationship('Wishlist', secondary=wishlist_listing, back_populates='listing', lazy='dynamic')
    tag = db.relationship('Tag', secondary=tag_listing, back_populates='listing', lazy='dynamic')
    promotion = db.relationship('Promotion', secondary=promotion_listing, back_populates='listing', lazy='dynamic')
    #cate = db.relationship('Cate', back_populates='listing', lazy=True, primaryjoin='Listing.cate_id == Cate.id')
    cate = db.relationship('Cate', secondary=cate_listing, lazy='dynamic', back_populates='listing')
    reviews = db.relationship('Review', backref='listing', lazy='dynamic')
    favorite = db.relationship('FavoriteProduct', backref='listing', lazy='dynamic')

    is_active = db.Column(db.Boolean(), default=True) #[sold, active,]
    deleted = db.Column(db.Boolean(), default=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def exists(Listing):
        return Listing.query.filter(Listing.id==Listing).first() is not None
    # Example: Unique constraint on the 'title' and 'cate_id' columns
    __table_args__ = (
        db.UniqueConstraint('title', 'cate_id', 'page_id', name='uq_title_cate_page'),
    )
    """ __table_args__ = (
        db.UniqueConstraint('title', 'cate_id', name='uq_title_cate'),
    ) """
    def __init__(self, color, location, contact, size):
        # Check and set the fields to None if they are empty or contain an empty JSON object
        if color is not None and not bool(color):
            self.color = None
        else:
            self.color = color

        if location is not None and not bool(location):
            self.location = None
        else:
            self.location = location

        if contact is not None and not bool(contact):
            self.contact = None
        else:
            self.contact = contact

        if size is not None and not bool(size):
            self.size = None
        else:
            self.size = size

class Cate(db.Model, SearchableMixin):  #levels-> (super1->main2->sub3->mini4)
    """ Self refferential multi-level/Nested categorization """
    __tablename__ = 'cate'
    __searchable__=['name', 'children', 'photo']
    id = db.Column(db.Integer, primary_key=True)
    lev = db.Column(db.Integer, default=0)
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(100))
    photo = db.Column(db.String(50))
    dept = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('cate.id'))
    children = db.relationship('Cate', backref='parent', remote_side=[id] )
    listing = db.relationship('Listing', secondary=cate_listing, lazy='dynamic', back_populates='cate')
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class Tag(db.Model):
    __tablename__ = 'tag'
    __searchable__=['name']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    listing = db.relationship('Listing', secondary=tag_listing, back_populates='tag', lazy='dynamic')

#can be comments/likes/dislikes/reviews/views
class Review(db.Model):
    __tablename__='review'
    __searchable__=['rating','content','replies','comments']
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    
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
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'))
    listing = db.relationship('Listing', secondary=promotion_listing, back_populates='promotion', lazy='dynamic')
    #items = relationship('PromotionListing', back_populates='promotion')

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    listing = db.relationship('Listing', secondary=wishlist_listing, back_populates='wishlist', lazy='dynamic')

class FavoriteProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)

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
    data={'listing_id': listing.id, 'item_name': item.name}
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
    #listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    cost = db.Column(db.Integer)
    dept = db.Column(db.String(80), nullable=False, default='k') #[k=kitchen, c=cocktail, b=bar]
    desc = db.Column(db.String(100)) #desc
    
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
   