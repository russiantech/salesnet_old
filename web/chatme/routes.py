from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import func 

from sqlalchemy.sql import or_ , and_

from web.models import db
from web.chatme.forms import MessageForm
from web.models import User, Chat

chat = Blueprint('chat', __name__)

#@chat.route('/chat', methods=['GET', 'POST'])
@chat.route('/chat/<string:usr>', methods=['GET', 'POST'])
@login_required
def chst(usr):
    usr = User.query.filter_by(username=usr).first_or_404()

    conversation = Chat.query.filter( and_(Chat.to == current_user, Chat.fro == usr) | \
        (and_(Chat.to == usr, Chat.fro == current_user) ) ).order_by(Chat.created.asc())
    
    chats = [c for c in conversation]

    form = MessageForm()
    flash(f'Your Chat {form.errors}.', 'danger') if not form.validate_on_submit() else ''
    if form.validate_on_submit():
        
        for msg in chats:
            msg.recent = False
            msg.seen = True
        
        msg = Chat(author=current_user, recipient=usr, body=form.message.data, recent=True) # recent=True)
        usr.notify('count_unread', usr.count_unread())
        db.session.add(msg)

        db.session.commit()
        flash(f'Your Chat Has Been Sent.', 'success')
    context = {'user':usr, 'form':form,  'chat': chats }
    return render_template('chatme/chat.html', **context )

"""db.session.query(UserModel.city).distinct().all()"""

@chat.route('/chat')
@login_required
def list():
    current_user.last_message_read_time = func.now()
    current_user.notify('count_unread', 0)
    db.session.commit()
    ct = Chat.query.filter(and_(or_(Chat.recipient_id == current_user.id, Chat.sender_id==current_user.id), Chat.recent==True ) ).order_by(Chat.created.desc())

    #conversation = Chat.query.filter(or_(Chat.to == current_user, Chat.from == current_user)).order_by(Chat.created.desc()).distinct()
    #conversation = Chat.query.filter( or_(current_user != Chat.to, current_user != Chat.from), and_(Chat.from == current_user, Chat.to == current_user)).distinct()
    #conversation = User.query.filter(or_(Chat.to == current_user, Chat.from == current_user) ).order_by(Chat.created.desc()).distinct() 
    """     conversation = User.query.filter(
        and_(Chat.to == current_user, Chat.from != None) |
        and_(Chat.from == current_user, Chat.to != None) ).order_by(Chat.created.desc()).distinct()  """
    #query = select(User.id, User.username, User.photo).where(or_(Chat.to == current_user, Chat.from == current_user)).distinct()

    context = { 
       # 'chat':  [ m for m in conversation ],
       # 'query': query,
        'chat':[c for c in ct],
    }
        
    return render_template('chatme/chatlist.html', **context)

#send message route
@chat.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Chat(author=current_user, recipient=user, body=form.message.data)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.add(msg)
        db.session.commit()
        flash( ('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('chatme/send_message.html', form=form, recipient=recipient)

