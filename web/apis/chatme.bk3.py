import jsonschema
from flask import Blueprint, jsonify, request, url_for
from flask_login import current_user
from web.models import db, Chat, User
from sqlalchemy import or_
from  web.extensions import socketio, limiter, redis
from web.apis.errors import bad_request, response

chat_api = Blueprint('chat_api', __name__)
# // General/(*) chat/conversations
# Define the JSON schema (as a Python dictionary)

event_schemas = {
    'save-chat-request': {
        "type": "object",
        "properties": {
            "to": { "type": "integer" },
            "fro": { "type": "integer" },
            "text": { "type": "string" },
            "sticker": { "type": "string" },
            "media": { "type": "string" },
            "client": { "type": "boolean", "default": True },
            "type": { "type": "string", "enum": ["connect", "discount", "typing", "chat"] }
        },
        "required": ["to", "fro"],
        "additionalProperties": False,
        "oneOf": [
            {
                "required": ["text"]
            },
            {
                "required": ["sticker"]
            },
            {
                "required": ["media"]
            },
            {
                "required": ["text", "sticker"]
            },
            {
                "required": ["text", "media"]
            },
            {
                "required": ["sticker", "media"]
            },
            {
                "required": ["text", "sticker", "media"]
            }
        ]
        },
    
    'fetch-chat-request': {
        "type": "object",
        "properties": {
            "user-id": { "type": "integer" }
        },
        "required": ["user-id"]
        },

    'remove-chat-request': {
        "type": "object",
        "properties": {
            "chat-id": {"type": "integer" },
            "user-id": {"type": "integer" }
        },
        "required": ["chat-id", "user-id"]
        },

    'remove-chat-request': {
        "type": "object",
        "properties": {
            "chat-id": {"type": "integer" },
            "user-id": {"type": "integer" },
            "chat-content": {"type": "string"}
        },
        "required": ["chat-id", "chat-content", "user-id"]
        },
}

import uuid, json
# Assuming that socketio is your SocketIO instance
class ConnectionManager:
    def connect(self, socket_id):
        user_id = current_user.id if current_user.is_authenticated else True
        # Use the Redis HSET command to set the connection with a field (socket_id)
        # and a value (user_id or True)
        redis.hset('active_connections', socket_id, user_id)

    def disconnect(self, socket_id):
        # Use the Redis HDEL command to remove the connection from the hash
        redis.hdel('active_connections', socket_id)

    def is_connected(self, socket_id):
        # Use the Redis HEXISTS command to check if the socket_id exists in the hash
        return redis.hexists('active_connections', socket_id)

    def send_chat_to(self, socket_id, message):
        if self.is_connected(socket_id):
            socketio.emit('chat', message, room=socket_id)

    def notify(self, socket_id, message):
        if self.is_connected(socket_id):
            socketio.emit('response', message, room=socket_id)

connection_manager = ConnectionManager()

payload = {
    'to' : 0,
    'fro' : 0,
    'text' : '',
    'sticker' : '',
    'media' : '',
    'client': False,
    "type": "", #[connect, discount, typing, chat(custom)]
    #"id": user_id
    }

@socketio.on('connect-request', namespace='/chat')
@limiter.limit("1 per second")
#@socketio.on('connect')
def handle_connect():
    user_id = request.sid
    payload['fro'] = user_id
    payload['type'] = 'connect'
    
    connection_manager.connect(user_id)

    #print(payload)

    connection_manager.send_chat_to(user_id, json.dumps(payload))

@socketio.on('disconnect-request', namespace='/chat')
def handle_disconnect():
    user_id = request.sid
    connection_manager.disconnect(user_id)

@socketio.on('typing-request', namespace='/chat')
def handle_typing(data):

    fro = request.sid

    if connection_manager.is_connected(data.to):
        """ create event to inform clients connected """
        payload = {"type": "typing", "fro": fro, "text": data.txt}
        connection_manager.send_chat_to(data.to, json.dumps(payload))
    else:
        """pass"""
        print('recipient not connected for', fro)
        # Handle the case when the recipient is not connected
        # You can notify the sender or take other appropriate actions
    print('data is:', data)

@socketio.on('save-chat-request', namespace='/chat')
def save(data):
    event_schema = event_schemas.get('save-chat-request')
    
    jsonschema.validate(data, event_schema)
    #pls validations here first
    if not (['fro','to'] and ('text' or 'sticker' or 'media') ) in data:
        #return bad_request('Can Not Send Blank Chats')
        data['error'] = True
        return connection_manager.notify(response.to, json.dumps(bad_request('Invalid payload')))

    if not User.user_exists(data.fro) and not User.user_exists(data.to):
        #return bad_request('Invalid User Id(s)')
        data['error'] = True
        return connection_manager.notify(data.fro, json.dumps(bad_request('Invalid user-ids')))
    
    chat = Chat()
    chat.from_dict(data, new_chat=True)
    db.session.add(chat)
    db.session.commit()
    response = chat.to_dict()
    #return response

    #if .to is online, tell f.from they're online
    if connection_manager.is_connected(data.to or request.sid):
        """update payload if .to is online/connected"""
        response['online'] = True 
    response['success'] = True
    return connection_manager.notify(response.to, json.dumps(response))

@socketio.on('fetch-chat-request', namespace='/chat')
#@token_auth.login_required
def fetch(data):
    if current_user.is_authenticated and not (data.id == current_user.id):
        data = bad_request('nah, it\'s a blank chat')
        data['error'] = True
        return connection_manager.notify(data.fro, json.dumps(data))
    chat = Chat.query.filter(or_(Chat.to == data.id, Chat.fro == data.id)).order_by(Chat.updated.desc())
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Chat.to_collection_dict(chat, page, per_page, 'chat_api.get_chat', id=id)
    #return jsonify(data)
    data['success'] = True
    connection_manager.notify(data.fro, json.dumps(data))

@socketio.on('remove-chat-request', namespace='chat')
def remove(data):  # Use 'id' as the parameter name
    chat = Chat.query.get(data.id)  # Replace 'chat_id' with 'id'
    if chat:
        if not (chat.fro == current_user.id or chat.to == current_user.id):
            return bad_request(message="Invalid Conversation Request")
        if chat.fro == current_user.id or request.sid:
            chat.fro_del = True
        else:
            chat.to_del = True
        db.session.commit()  # Commit the session once
        #return response('Success! Chat Removed For You')
        if connection_manager.is_connected(data.to or request.sid):
            """update payload if .to is online/connected"""
            data['online'] = True 
    data['error'] = True 
    connection_manager.notify(data.to, json.dumps(data))

@socketio.on('update-chat-request')
def update(data):
    if data.id is None:
        return bad_request('chat id is missing in the request data')
    chat = Chat.query.get(data.id)
    if chat is None:
        return bad_request('chat not found')
    
    if not (chat.fro == current_user.id):
        return bad_request(message="invalid request, it's not ur chat")
    
    chat.from_dict(data, new_chat=False)
    db.session.commit()

    data = chat.to_dict()
    data['success'] = True
    if connection_manager.is_connected(data.to or request.sid):
        """update payload if .to is online/connected"""
        data['online'] = True 
    connection_manager.notify(data.to, json.dumps(data))

