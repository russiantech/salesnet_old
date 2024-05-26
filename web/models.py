import base64, os, json
from hashlib import md5
from datetime import datetime, timedelta
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, and_, desc, or_
from sqlalchemy.orm import aliased
db = SQLAlchemy()
from web.utils.custom_mixins import  SearchableMixin, PaginatedAPIMixin #ensure db is instantiated/initialized b4 this very import to prevent circular import, just like this
#class BaseModel(Base, db.Model):
class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, unique=True, autoincrement=True, primary_key=True, nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    deleted = db.Column(db.Boolean(), default=False)
    active =  db.Column(db.Boolean(), default=True)

category_listing = db.Table(
    'category_listing',
    db.Model.metadata,
    db.Column('cate_id', db.Integer, db.ForeignKey('category.id')),
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
user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    keep_existing=True
)
# Create a table to represent the many-to-many relationship between roles and permissions
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)

followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

""" chat_participants = db.Table(
    'chat_participants',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('chat_id', db.Integer, db.ForeignKey('chat.id'), primary_key=True),
    db.Column('is_sender', db.Boolean, nullable=False),  # Added is_sender column

   # user = db.relationship('User', back_populates='chats'),
    #chat = db.relationship('Chat', back_populates='participants') 
) """

# Association table for many-to-many relationship between User and ChatRoom
# Users are linked to chat_room & chat_room links to Chat
user_chat_room = db.Table('user_chat_room',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('chat_room_id', db.Integer, db.ForeignKey('chat_room.id'), primary_key=True)
)

class Brand(db.Model, PaginatedAPIMixin):
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

class User(db.Model, SearchableMixin, PaginatedAPIMixin, UserMixin):
    __searchable__ = ['name', 'username', 'email', 'phone', 'about']
    id = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    name = db.Column(db.String(100), index=True)
    username = db.Column(db.String(100), index=True, nullable=False, unique=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, index=True)  #str type recommended bcos they're not meant for calculations
    password = db.Column(db.String(500), index=True, nullable=False)
    contact = db.Column(db.JSON, default=None) #{'city': 'lagos', 'region':'nigeria', 'street': 'palm street, lekki'}
    avatar = db.Column(db.String(1000))
    photos = db.Column(db.String(1000))
    gender = db.Column(db.String(50))  # ['male','female','other']
    about = db.Column(db.String(5000))
    bank = db.Column(db.JSON, default=None) # socials: { 'bank': 'Opay', 'acct_no':'7026561327' }
    socials = db.Column(db.JSON, default=None) # socials: { 'fb': '@chrisjsm', 'insta': '@chris', 'twit': '@chris','linkedin': '', 'whats':'@techa' }
    src = db.Column(db.String(50))
    category = db.Column(db.String(50))
    ip = db.Column(db.String(50))
    online = db.Column(db.Boolean(), default=False)  # 1-online, 0-offline
    status = db.Column(db.Boolean(), default=True)  # [ active(1), not active(0)]
    verified = db.Column(db.Boolean(), default=False)  # verified or not
    is_vendor = db.Column(db.Boolean, default=False, nullable=False)

    chat_rooms = db.relationship('ChatRoom', secondary=user_chat_room, back_populates='users')
    #//chats = db.relationship('Chat',  back_populates='users', lazy=True)
    chats = db.relationship('Chat',  backref='users', lazy=True)

    # Define relationships for both buying and selling
    #vendors = db.relationship('Vendor', backref='user', lazy=True)
    pages = db.relationship('Pages', back_populates='user') #instead of vendors we have pages(sales page(s))
    #listing = db.relationship('Listing', backref='user', lazy='dynamic')
    listing = db.relationship('Listing', back_populates='user',  lazy='dynamic') #instead of products, we have listing
    orders = db.relationship('Order', backref='user', lazy=True)
    addresses = db.relationship('Address', backref='user', lazy=True)
    shipping_addresses = db.relationship('ShippingAddress', backref='user', lazy=True)
    notifications = db.relationship("Notification", backref="users", lazy=True) 
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    wishlist = db.relationship('Wishlist', backref='user', lazy='dynamic')
    favorites = db.relationship('FavoriteProduct', backref='user', lazy='dynamic')
    promotions = db.relationship('Promotion', backref='user', lazy='dynamic')
    analytics = db.relationship('AnalyticsEvent', backref='user', lazy='dynamic')
    roles = db.relationship('Role', secondary=user_roles, back_populates='user', lazy='dynamic')
    followed = db.relationship('User', secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id), backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted
    
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_listing(self):
        followed = Listing.query.join(followers, (followers.c.followed_id == Listing.user_id)).filter(followers.c.follower_id == self.id)
        own = Listing.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Listing.timestamp.desc())
    
    def followed_pages(self):
        followed = Pages.query.join(followers, (followers.c.followed_id == Pages.user_id)).filter(followers.c.follower_id == self.id)
        own = Pages.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Pages.timestamp.desc())
    
    def avater(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    """ def get_reset_password_token(self, expires_in=600):
        return jwt.encode({'reset': self.id, 'exp': time() + expires_in}, current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset']
        except:
            return
        return User.query.get(id) """
    
    def get_token(self, expires_in=3600):
        """ for-api """
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        """ for api """
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user
    # ...
    def to_dict(self, included_only=None, include_email=False):
        fro_avatar_url = self.avater(128)
        data = {
            'id': self.id,
            'name': self.name,
            'avatar': self.avatar or 'avatar.svg',
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'photos': self.photos,
            'contact': json.loads(str(self.contact)) if self.contact else None,
            'about': self.about,
            'bank': json.loads(str(self.bank)) if self.bank else None,
            'socials': json.loads(str(self.socials)) if self.socials else None,
            'gender': self.gender,
            'category': self.category,
            'online': self.online,
            'verified': self.verified,
            'is_vendor': self.is_vendor,
            'page_name': [page.title for page in self.pages], #self.pages.users.title,
            'last_seen': self.updated.isoformat() + 'Z',
            'listing_count': self.listing.count(),
            'follower_count': self.followers.count(),
            'followed_count': self.followed.count(),
            '_links': {
                'self': url_for('main.user', username=self.username),
                'followers': url_for('user_api.get_followers', id=self.id),
                'followed': url_for('user_api.get_followed', id=self.id),
                'avatar': self.avater(128)
                #'avatar': fro_avatar_url
            }
        }
        if include_email:
            data['email'] = self.email
        
        if included_only:
            data = { 
                x : self.x for x in included_only
            }

        return data
    
    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    @staticmethod
    def user_exists(id_or_username):
        user = User.query.filter(or_(User.id == id_or_username, User.username == id_or_username)).first()
        return user

    def user_exist(id):
        user = User.query.filter_by(id=id).first()
        return user
    
    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.username}')"

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(120), nullable=True)

    #chat = db.relationship('Chat', backref='chat_room', lazy=True)
    chats = db.relationship('Chat', backref='chat_rooms', lazy=True)
    #//chats = db.relationship('Chat', back_populates='chat_rooms', lazy=True)
    users = db.relationship('User', secondary=user_chat_room, back_populates='chat_rooms')
        # Example: Unique constraint on the 'title' and 'cate_id' columns
    __table_args__ = (
        db.UniqueConstraint('id', 'name', 'description', name='uq_id_name_description'),
    )

    def __init__(self, name='', description=''):
        self.name = name
        self.description = description
        
    def create_room(users, name='', description=''):
        """
        Create a chat room for the given users and return details about the room.

        :param users: List of User instances to be added to the chat room.
        :param name: Name for the chat room (optional).
        :param description: Description for the chat room (optional).
        :return: Dictionary containing details about the created room.

        :Sample-usage:
            # Assume user and chat_room are instances of the User and ChatRoom models, respectively.
            # Create a room for a single user
            room_details_single_user = chat_room.create_room(users=[user])

            # Create a room for multiple users
            users_list = [user1, user2, user3]  # List of User instances
            room_details_multiple_users = chat_room.create_room(users=users_list, name='Custom Room', description='Custom description')
        """
        # Create a new chat room with the provided name and description
        new_room = ChatRoom(name=name, description=description)

        new_room.users.extend(users)

        db.session.add(new_room)
        db.session.commit()

        # Add users to the chat room
        #new_room.users.extend(users)
        #db.session.commit()

        # Return details about the created room
        room_details = {
            'room_id': new_room.id,
            'room_name': new_room.name,
            'description': new_room.description,
            'users': [user.username for user in users],
        }

        return room_details

#chatroom_instance = ChatRoom()

class Chat(db.Model, PaginatedAPIMixin):
    __tablename__ = 'chat'

    id = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)

    # Create a relationship that uses the backref argument
    #chat_rooms = db.relationship('ChatRoom', back_populates='chats', lazy=True)    
    #users = db.relationship('User', back_populates='chats', lazy=True)    
    
    #// DO NOT FORGET THESE 2 WHEN INSERTING CHATS (chat.chatrooms & chat.users)

    text = db.Column(db.String(140))
    media = db.Column(db.String(140))
    sticker = db.Column(db.String(140))

    seen = db.Column(db.Boolean(), default=False, nullable=False)
    last_seen = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    recent = db.Column(db.Boolean(), default=True, nullable=False)
    fro_del = db.Column(db.Boolean(), default=False, nullable=False)
    to_del = db.Column(db.Boolean(), default=False, nullable=False)
    
    deleted = db.Column(db.Boolean(), default=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
            CheckConstraint(
                "text IS NOT NULL OR sticker IS NOT NULL OR media IS NOT NULL",
                name="at_least_one_content_check",
            ),
        )


    def to_dict(self):
        
        q = db.session.query(ChatRoom).filter(self.chat_room_id == ChatRoom.id)
        
        if len(q.all()) > 0:
             
            user = {
                'name': [x.name for x in q[0].users if x.id == self.user_id] + [x.name for x in q[0].users if x.id != self.user_id],  # Ensure sender appears first
                'avatar': [x.avatar for x in q[0].users if x.id == self.user_id] + [x.avatar for x in q[0].users if x.id != self.user_id],  # Ensure sender appears first

            'unread_count': self.unread_count(chat_room_id=self.chat_room_id, user_id=self.user_id),
            'user_id': self.user_id,
            'chat_room_id': self.chat_room_id,
            'is_sender': self.user_id == current_user.id, #True/False. This assumes that current_user is the logged in user
            #'is_sender':  [ True for x in q[0].users if x.id == self.user_id ] ,
            #####///////////////////
            'sender_name': [x.name for x in q[0].users if x.id == self.user_id] ,
            'sender_avatar': [x.avatar for x in q[0].users if x.id == self.user_id]

            }
        else:
            user = {}
            
        data = {
            'id': self.id,
            **user, #unpacking
            'text': self.text if self.text else '',
            'sticker': self.sticker,
            'media': self.media,
            'seen': self.seen,
            'recent': self.recent,
            'last_message': self.text if self.text and self.recent else None,
            'fro_del': self.fro_del,
            'to_del': self.to_del,
            'created': self.created.isoformat() + 'Z' if self.created is not None else None,
            'updated': self.updated.isoformat() + 'Z' if self.updated is not None else None,
        }
        #print(data)
        return data

    #microsoft's bing chat
    def from_dict(self, data, new_chat=False):
        if new_chat:
            for field in self.to_dict().keys():
                if field in data:
                    setattr(self, field, data[field])

            # Add the chat to the database and commit to get the chat_id
            """ db.session.add(self)
            db.session.commit() """

            """ if 'users' in data:
                users = data['users']
                # Assuming 'chats' is the backref in User model
                for user in users:
                    user.chats.append(self) """

            """ if 'users' in data:
                #self.user.extend(user for user in data['users'])
                #self.users.append(user for user in data['users'])
                for user in data['users']:
                    self.users = user  """

    @classmethod
    def mark_recent_false(cls, room_id, current_user, to_user):
        # Now set the most recent conversation to True
        most_recent_chat = (
            cls.query.join(ChatRoom)
            .filter(ChatRoom.id == room_id, ChatRoom.users.contains(current_user), ChatRoom.users.contains(to_user))
            .order_by(desc(cls.created)).all()
        )

        for recent in most_recent_chat:
            recent.recent = False

        # Optionally, you can commit the changes to the database
        #db.session.commit()

    @classmethod
    def unread_count(cls, chat_room_id, user_id):
        """
        Get the number of unread converation in a specific chat room for the given user.

        :param chat_room_id: ID of the chat room.
        :param user_id: ID of the user.
        :return: Number of unread messages.

        :Usage:
            # Assuming chat_room_id is the ID of the chat room and user_id is the ID of the user.
            unread_messages_count = Chat.unread_count(chat_room_id=chat_room_id, user_id=user_id)
            print(f"Number of unread messages: {unread_messages_count}")

        """
        unread_chat_count = (
            cls.query
            .filter(and_(cls.chat_room_id == chat_room_id, cls.seen == False, cls.user_id != user_id))
            .count()
        )

        return unread_chat_count

    def __repr__(self):
        return '<Chat {}>'.format(self.text)
    # Remember to define the relationship between the `Chat` and `User` models.

class Pages(db.Model, SearchableMixin):
    __tablename__ = 'pages'
    __searchable__ = ['name', 'username', 'email', 'phone', 'about']
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    desc = db.Column(db.Text, nullable=True)
    images = db.Column(db.String(1000))
    socials = db.Column(db.JSON, default=None) # socials: { 'fb': '@chrisjsm', 'insta': '@chris', 'twit': '@chris','linkedin': '', 'whats':'@techa' }
    location = db.Column(db.JSON) #location:- {'region':'USA', 'city':'london', 'street':'beach-house, 27 california', 'zipcode':'1099990'},
    contact = db.Column(db.JSON) #contact:- see location column for sample using(emal:email,phone:phone,etc)
    bank = db.Column(db.JSON) #cmultiple({'opay':702656127, 'fcmb':5913408010})
    password = db.Column(db.String(500), index=True, nullable=False)
    reviews = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='pages')

    listing = db.relationship('Listing', back_populates='pages', lazy='dynamic')
    promotions = db.relationship('Promotion', backref='page', lazy=True)
    deleted = db.Column(db.Boolean(), default= 0)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class Notification(db.Model, PaginatedAPIMixin):
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
    user = db.relationship('User', secondary=user_roles, back_populates='roles', lazy='dynamic') #FK linking role->user(many->many-rel)
    permissions = db.relationship('Permission', secondary=role_permissions, backref='roles', lazy='dynamic')

class Listing(db.Model, SearchableMixin, PaginatedAPIMixin):
    __tablename__ = 'listing'
    __searchable__ = [
        'cate_id','title','price', 'desc', 'images', 'currency','location','contact','page_id','user_id', 'pay_interval', 'condition',
        'negotiable', 'phone', 'about',
        'required_skills','meet_up', 'ip', 'availability', 'company', 'sku', 'stock_qty', 'discount','color', 'size','property_size', 
        'model','year','make','job_level','min_exp','min_qualify','pay_range','responsibilities','job_setup', 'required_skills',
        'bedrooms', 'bathrooms','property_for', 'amenities', 'amenities', 'listing_brand','address', 'date_available', 'listing_type',
        'fuel_type']
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cate_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    title = db.Column(db.String(80), nullable=False)
    images = db.Column(db.JSON, nullable=False)
    currency = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    pay_interval = db.Column(db.String(50)) #like monthly for listing like property, like maybe commission-based for listing like jobs/services
    desc = db.Column(db.Text)
    negotiable = db.Column(db.Boolean(), default=False)
    listing_type = db.Column(db.String(50), nullable=False, default='physical') 
    listing_brand = db.Column(db.String(50))  
    condition =  db.Column(db.String(50)) #(New, Used like new, Used good, Used fair)
    ip = db.Column(db.String(50))
    meet_up = db.Column(db.JSON)
    availability  = db.Column(db.String(50)) #instock,single item,avaialable,//Will be updated to 'sold' if initially a single item and it's sold,
    company = db.Column(db.String(50))

    #Listings
    sku = db.Column(db.String(1000), unique=True) #(stock keeping unit)
    stock_qty = db.Column(db.Integer, default='1')
    discount = db.Column(db.Integer)
    
    color = db.Column(db.JSON, default=None, nullable=True) #color:- {'red','wine', 'etc'},
    size = db.Column(db.JSON, default=None, nullable=True) #size:- {'s','m', 'l', 'xl', 'xxl'},

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

    location = db.Column(db.JSON, nullable=True) #location:- {'region':'USA', 'city':'london', 'street':'beach-house, 27 california', 'zipcode':'1099990'},
    contact = db.Column(db.JSON, nullable=True) #contact:- see location column for sample using(name:name,emal:email,phone:phone,etc)
    
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'))
    pages = db.relationship('Pages', back_populates='listing')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='listing')
    
    wishlist = db.relationship('Wishlist', secondary=wishlist_listing, back_populates='listing', lazy='dynamic')
    tag = db.relationship('Tag', secondary=tag_listing, back_populates='listing', lazy='dynamic')
    promotion = db.relationship('Promotion', secondary=promotion_listing, back_populates='listing', lazy='dynamic')
    #category = db.relationship('Category', back_populates='listing', lazy=True, primaryjoin='Listing.cate_id == Category.id')
    category = db.relationship('Category', secondary=category_listing, lazy='dynamic', back_populates='listing')
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
    """ def __init__(self, color, location, contact, size):
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
            self.size = size """
    
    def parse_json(self, json_str):
        try:
            if json_str:
                return json.loads(str(json_str))
        except json.JSONDecodeError:
            # Handle the case where json_str is empty or invalid JSON
            return None

    def parse_str(self, str):
        try:
            if str is None or str == "":
                return None
            return str
        except AttributeError:
            # Handle the case where json_str is empty or invalid JSON
            return None
    
    def to_dict(self):
        data = {
            'id': self.id,
            'ip': self.ip,
            'title': self.title,
            'price': self.price,
            'desc': self.desc,
            'cate_id': self.cate_id,
            'condition': self.condition,
            'currency': self.currency,
            'contact': self.parse_json(self.contact)  if self.contact else None,
            'location': self.parse_json(self.location) if self.location else None,
            'images': self.parse_json(self.images) if self.images else None,
            'amenities': self.parse_json(self.amenities)if self.amenities else None,
            'size': self.parse_json(self.size) if self.size else None,
            'color': self.parse_json(self.color) if self.color else None,
            'meet_up': self.meet_up,
            'pay_interval': self.pay_interval,
            'negotiable': self.negotiable,
            'availability': self.availability,
            'listing_type': self.listing_type,
            'listing_brand': self.listing_brand,
            'sku': self.sku,
            'stock_qty': self.stock_qty,
            'company': self.company,
            'discount': self.discount,

            'property_size': self.property_size,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'property_for': self.parse_str(self.property_for),
            'date_available': self.date_available,

            'fuel_type': self.fuel_type,
            'make': self.make,
            'model': self.model,
            'year': self.year,

            'job_level': self.job_level,
            'min_exp': self.min_exp,
            'min_qualify': self.min_qualify,
            'pay_range': self.pay_range,
            'responsibilities': self.responsibilities,
            'required_skills': self.parse_str(self.required_skills),
            'job_setup': self.job_setup,
            'listing_profile': url_for('listing_api.get_listing', id=self.id),

            'page': {
                'id':  self.pages.id if self.pages else None,
                #'title':  self.parse_str(self.pages.title),
                'title':  self.parse_str(self.pages.title) if self.pages else None,
                'desc': self.parse_str(self.pages.desc) if self.pages else None,
                'bank': self.parse_json(self.pages.bank) if self.pages else None,
                'contact': self.parse_json(self.pages.contact)  if self.pages else None,
                'location': self.parse_json(self.location) if self.pages else None,
                'images': self.parse_json(self.pages.images) if self.pages else None,
                'socials': self.parse_json(self.pages.socials) if self.pages else None,
                'reviews': (self.pages.reviews) if self.pages else None,
                'page_user_id': (self.pages.user_id) if self.pages else None,
                'page_user': (self.pages.user.id) if self.pages else None,
            },

            'user': {
                'page_url':  None,
                'user_name': (self.user.name or self.user.username) if self.user else None,
                'location': (self.user.location or self.page.location) if self.user else None,
                'user_name': (self.user.name or self.user.username) if self.user else None,
            },
            
            '_links': {
                'user_profile': url_for('user_api.get_user', id=self.user_id) if self.user_id else None,
                'self': url_for('listing_api.get_listing', id=self.id),
                'followers': url_for('listing_api.get_followers', id=self.id),
                'followed': url_for('listing_api.get_followed', id=self.id)
            }

        }

        return data
    
    def from_dict(self, data, new_listing=False):
        for field in self.__searchable__:
            if field in data:
                setattr(self, field, data[field])
        if 'contact' in data:
            self.contact(json.dumps(data['contact']))
        if 'location' in data:
            self.location(json.dumps(data['location']))
        if 'images' in data:
            self.images(json.dumps(data['images']))
        if 'color' in data:
            self.color(json.dumps(data['color']))
        if 'size' in data:
            self.size(json.dumps(data['size']))
        if 'amenities' in data:
            self.amenities(json.dumps(data['amenities']))

    """     def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password']) """

class Category(db.Model, SearchableMixin, PaginatedAPIMixin):  #levels-> (super1->main2->sub3->mini4)
    """ Self refferential multi-level/Nested categorization """
    __tablename__ = 'category'
    __searchable__=['name', 'children', 'photo']
    id = db.Column(db.Integer, primary_key=True)
    lev = db.Column(db.Integer, default=0)
    name = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.String(100))
    photo = db.Column(db.String(50))
    dept = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    children = db.relationship('Category', backref='parent', remote_side=[id] )
    listing = db.relationship('Listing', secondary=category_listing, lazy='dynamic', back_populates='category')
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
class Review(db.Model, PaginatedAPIMixin):
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

class Order(db.Model, PaginatedAPIMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shipping_address = db.relationship('ShippingAddress', backref='order', lazy='dynamic')
    order_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    order_status = db.Column(db.String(100), nullable=False) #ordered, pending etc
    items = db.relationship('OrderItem', backref='order', lazy=True)

    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    deleted = db.Column(db.Boolean(), default=False)  # 0-deleted, 1-not-deleted

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    order_qty = db.Column(db.Integer, nullable=False)
    order_time = db.Column(db.DateTime, default=datetime.utcnow)

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
   