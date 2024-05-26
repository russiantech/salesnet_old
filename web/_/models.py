
#from itsdangerous.url_safe import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.ext.declarative import declarative_base
import json , time , datetime
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
#from itsdangerous import TimedSerializer as Serializer
from flask_login import UserMixin, current_user
from sqlalchemy.sql import func
from flask import current_app
from web import db, s_manager

Base = declarative_base()
metadata = Base.metadata

# @s = @signin
@s_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

#class BaseModel(Base, db.Model):
class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, unique=True, autoincrement=True, primary_key=True, nullable=False)
    created = db.Column(db.DateTime(timezone=True),  index=True, auto_now_add=True)
    updated = db.Column(db.DateTime(timezone=False),  index=True, onupdate=func.now())
    deleted = db.Column(db.Boolean(), default=False)
    active =  db.Column(db.Boolean(), default=True)


#associations <according to bluehost, best-practice is to use is to use a table instead of a database model. db.table()
course_tag = db.Table('course_tag',
    db.Column('cid', db.Integer, db.ForeignKey('course.id'), primary_key=True),
    db.Column('tid', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
    )

usr_korse = db.Table('usr_korse',
    #db.Column('uid', db.Integer, db.ForeignKey('user.id'), primary_key=True, default=[current_user.id if current_user else None]),
    db.Column('uid', db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=True),
    db.Column('cid', db.Integer, db.ForeignKey('course.id'), primary_key=True)
    )

cate_korse = db.Table('cate_korse',
    db.Column('cid', db.Integer, db.ForeignKey('course.id')),
    db.Column('catid', db.Integer, db.ForeignKey('category.id'))
)

class Brand(BaseModel):
    __tablename__ = 'brand'
    type = db.Column(db.String(100), unique=True, nullable=False, default='Softwares')
    name = db.Column(db.String(100), unique=True, nullable=False, default='Russian Developers')
    email = db.Column(db.String(100), unique=True, index=True, nullable=False, default='softwares@russian.com')
    phone = db.Column(db.String(20), unique=True)
    photo = db.Column(db.String(1000))
    title = db.Column(db.String(50))
    logo = db.Column(db.Text())  # ['male','female','other']
    city = db.Column(db.String(50))
    lang = db.Column(db.String(100))
    us = db.Column(db.String(1000))
    ceo = db.Column(db.String(500))
    hype = db.Column(db.String(10000))  #slogan
    tutors = db.Column(db.Integer)  # course count for instructor
    ratings = db.Column(db.Integer)
    reviews = db.Column(db.Integer)
    bank = db.Column(db.String(100), default='fcmb')
    acct = db.Column(db.Integer, default=5913408010)
    status = db.Column(db.Boolean(), default=True)
    verified = db.Column(db.Boolean(), default=False)


class User(BaseModel, UserMixin):
    __tablename__ = 'user'
    name = db.Column(db.String(100), index=True)
    username = db.Column(db.String(100), index=True, nullable=False, unique=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, index=True)  #str type recommended bcos they're not meant for calculations
    password = db.Column(db.String(500), index=True, nullable=False)
    photo = db.Column(db.String(1000))
    title = db.Column(db.String(50))
    gender = db.Column(db.String(20))  # ['male','female','other']
    #gender = db.Column(db.Enum('0', '1', '2'))  # ['male','female','other']
    city = db.Column(db.String(50))
    lang = db.Column(db.String(100))
    about = db.Column(db.String(5000))
    socials = db.Column(db.JSON) # socials: { 'fb': '@chrisjsm', 'insta': '@chris', 'twit': '@chris','linkedin': '', 'whats':'@techa' }
    # instructors
    duration = db.Column(db.String(100))  # hours per week
    education = db.Column(db.String(100))
    korse_count = db.Column(db.Integer) # course count for instructor
    trainee = db.Column(db.Integer)  
    ratings = db.Column(db.Integer)
    reviews = db.Column(db.Integer)
    # students

    verified = db.Column(db.Boolean(), default=False)  # verified or not(users)
    graduated = db.Column(db.Boolean(), default=False)

    bank = db.Column(db.Integer)
    online = db.Column(db.Boolean(), default=False)  # 1-online, 0-offline
    last_seen = db.Column(db.DateTime)

    korse = db.relationship('Course', secondary=usr_korse, lazy=True)  # user->course(many-many) // backref='user',
    result = db.relationship("Result", backref='candidate', lazy=True)  # result->user
    fback = db.relationship("Feedback", backref='author', lazy=True)  # feedback->user
    quiz = db.relationship("Quiz", backref='candidate', lazy=True)  # quiz->user

    msg_sent = db.relationship('Message', foreign_keys='Message.sender', backref='author', lazy='dynamic')
    msg_received = db.relationship('Message', foreign_keys='Message.recipient', backref='receiver', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')


class Course(BaseModel):
    __tablename__ = 'course'
    photo = db.Column(db.String(20), nullable=False, default='default.png')
    title = db.Column(db.String(50), unique=True, nullable=False)
    desc = db.Column(db.Text,  unique=True, nullable=False)
    video = db.Column(db.String(1000))
    material = db.Column(db.String(100))
    fee = db.Column(db.Integer)
    lang = db.Column(db.String(30), default='english') 
    duration = db.Column(db.Integer)
    level = db.Column(db.String(30), default='pro')  # ['Novice',"Beginner","Pro", 'Expert', 'advanced']
    views = db.Column(db.Integer, nullable=True)  # count views
    comment = db.Column(db.Integer, nullable=True)  # comment count
    rating = db.Column(db.Integer, nullable=True)  # ratings count 

    completedby = db.Column(db.Integer, nullable=True)  # count those that complete d course
    status = db.Column(db.Enum('0', '1'), default='1')  # ["published","unpublished",]

    usr = db.relationship('User', secondary=usr_korse)
    #cat = db.relationship("Category", backref="course", lazy=True)  # category->course
    cat = db.relationship('Category', secondary=cate_korse, backref=db.backref('course', lazy='dynamic'), lazy='dynamic')

    chapt = db.relationship("Chapter", backref="course", lazy=True)  # chapter->course
    badg = db.relationship("Badge", backref="course", lazy=True)  # badge->course
    quiz = db.relationship("Quiz", backref="course", lazy=True)  # quiz->course
    reslt = db.relationship("Result", backref="course", lazy=True)  # result->course
    fback = db.relationship("Feedback", backref="course", lazy=True)  # feedback->course
    tm = db.relationship('Time', backref='course')
    tag = db.relationship('Tag', secondary=course_tag)

class Category(BaseModel):
    __tablename__ = 'category'
    title = db.Column(db.String(45), unique=True, nullable=False)
    desc = db.Column(db.String(100), unique=True)
    photo = db.Column(db.String(50))
    slug = db.Column(db.String(130))


class Chapter(BaseModel):
    __tablename__ = 'chapter'
    title = db.Column(db.String(50), nullable=False)
    desc = db.Column(db.Text)
    video = db.Column(db.String(1000))
    material = db.Column(db.String(100))
    fee = db.Column(db.Integer) # optional for chapters
    lang = db.Column(db.String(20), default='english')  #['english','spanish','french','arab','pidgin','chinese']
    duration = db.Column(db.Integer,  default=168) #defaults to 1 week, 178hrs in a week
    status = db.Column(db.String(20), default='pulished')  # ['published','unpublished','pending']

    korse = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # chapter->course->foreign-key
    usr = db.Column(db.Integer, db.ForeignKey('user.id'), default=1, nullable=True)  # instructor->chapters->foreign-key

    #DON'T FORET backref 'course' from Course Model when inserting data, even for all others

class Sections(BaseModel):
    __tablename__ = 'sections'
    topic = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    video = db.Column(db.String(1000))
    material = db.Column(db.String(100))
    duration = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), default='pulished')  # ['published','unpublished','pending']

    korse = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # chapter->course->foreign-key
    chapt = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)  # chapter->course->foreign-key


class Progress(BaseModel):
    __tablename__ = 'progress'
    level = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    usr = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # student-Fk
    korse = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # course Fk


class Quiz(BaseModel):
    __tablename__ = 'quiz'
    ask = db.Column(db.String(10000), nullable=False, unique=True)
    correct = db.Column(db.String(50), nullable=False)
    ans1 = db.Column(db.String(50), nullable=False)
    ans2 = db.Column(db.String(50), nullable=False)
    ans3 = db.Column(db.String(50), nullable=False)
    ans4 = db.Column(db.String(50))
    duration = db.Column(db.DateTime(timezone=True))
    level = db.Column(db.String('40'), default='pro')  # ['novice','pro','expert']

    korse = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # course Fk
    usr = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # course Fk


class Badge(BaseModel):
    __tablename__ = 'badge'
    level = db.Column(db.Integer)
    icon = db.Column(db.String(100))
    usr = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # student-Fk
    korse = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # course Fk


class Result(BaseModel):
    __tablename__ = 'result'
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)  # total
    usr = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # student-Fk
    korse = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # course Fk


class Feedback(BaseModel):
    __tablename__ = 'feedback'
    rating = db.Column(db.Integer)  # ranges from 1(worst) to 5(best)
    comment = db.Column(db.Text)  # comment/feed-back texts
    usr = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # user->feedback
    korse = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # user->course

class Time(BaseModel):
    __tablename__ = 'time'
    time = db.Column(db.Integer, nullable=False)  # time spent on course
    usr = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # user->feedback
    korse = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # user->course


class Post(BaseModel):
    __tablename__ = 'post'
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


class Tag(BaseModel):
    __tablename__ = 'tag'
    name = db.Column(db.String(50), nullable=False)
    korse = db.relationship('Course', secondary=course_tag, backref='ctag')

    def __repr__(self):
        return f'<Tag "{self.name}">' 



class Message(BaseModel):
    __tablename__ = 'message'
    sender = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    #notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<Message {}>'.format(self.body)

class Notification(BaseModel):
    __tablename__ = 'notifications'
    name = db.Column(db.String(128), index=True)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))
