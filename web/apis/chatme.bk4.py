import jsonschema, json
from flask import Blueprint, request
from flask_login import current_user
from web.models import db, Chat, User
from sqlalchemy import or_
from web.extensions import socketio, limiter, redis
from web.apis.errors import bad_request

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
            "sticker": { "type": "string"},
            "media": {"type": "string" },
            #"client": { "type": "boolean", "default": True },
            #"type": { "type": "string", "enum": ["connect", "discount", "typing", "chat"] }
        },
        "required": ["to", "fro"],
        #"required": ["to"],
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
        #"required": ["user-id"] #bcos it can also be gotten from socket-connections mapped
        },

    'remove-chat-request': {
        "type": "object",
        "properties": {
            "chat-id": {"type": "integer" },
            "user-id": {"type": "integer" }
        },
        "required": ["chat-id", "user-id"]
        },

    'update-chat-request': {
        "type": "object",
        "properties": {
            "chat-id": {"type": "integer" },
            "user-id": {"type": "integer" },
            "chat-content": {"type": "string"}
        },
        "required": ["chat-id", "chat-content", "user-id"]
        },

    'typing-request': {
        "type": "object",
        "properties": {
            "to": {"type": "integer" },
            "fro": {"type": "integer" },
        },
        "required": ["to", "fro"]
        },
}

class ConnectionManager:
    
    def connect(self, socket_id):
        user_id = current_user.id if current_user.is_authenticated else True
        # Use the Redis HSET command to set the connection with a field (socket_id)
        # and a value (user_id or True)
        return redis.hset('active_connections', socket_id, user_id)

    def disconnect(self, socket_id):
        # Use the Redis HDEL command to remove the connection from the hash
        return redis.hdel('active_connections', socket_id)

    def is_connected(self, socket_id):
        # Use the Redis HEXISTS command to check if the socket_id exists in the hash
        return redis.hexists('active_connections', socket_id)
    
    def get_active_connections(self):
        # Use the Redis HGETALL command to retrieve all active connections from the hash
        connections = redis.hgetall('active_connections')
        print(f'active-connections: {connections}')
        return connections
    
    """ def get_socket(self, user_id):
        #gets socket-id based on user-id provided 
        for socket in self.get_active_connections():
            if socket['user_id'] == user_id:
                return socket['socket_id'] or socket.sid
        return None """
    def get_socket(self, uid):
        """ Get socket-id based on user-id provided """
        for socket_id, user_id in self.active_connections.items():
            if user_id == uid:
                return socket_id
        return None


    def connected_user(self, socket_id):
        # Use the Redis HGET command to get the user ID associated with the socket ID
        #Reprs our authenticated user in this case.
        """ Will get connected socket user-d based on connected socket sid  """
        user_id = redis.hget('active_connections', socket_id)
        # Return the user ID
        return user_id
    
    #socket-user-making-request at the moment
    def connected_socket(self):
        return request.sid
    
    def notify(self, response_event, socket_id, msg):
        """ args:event, msg """
        if self.is_connected(socket_id):
            print(f'notifyer says not connected: {msg}')
            socketio.emit(response_event, msg, room=socket_id)
           #return socketio.emit(response_event, msg, room=socket_id)
        
connection_manager = ConnectionManager()

@socketio.on('connected', namespace='/chat')
@limiter.limit("1 per second")
def handle_connect(data):
    print(data)
    sid = request.sid
    connection_manager.connect(sid)
    print(f"Connected:- sid-{sid} : uid:- {connection_manager.connected_user(sid)}")

@socketio.on('disconnected', namespace='/chat')
def handle_disconnect():
    sid = request.sid
    connection_manager.disconnect(sid)
    print(f"Disconnected:- sid-{sid} : uid:- {connection_manager.connected_user(sid)}")

@socketio.on('typing-request', namespace='/chat')
def handle_typing(data):
    print(f'typing data: {data}')
    event_schema = event_schemas.get('typing-request')
    if not jsonschema.validate(data, event_schema):
        return connection_manager.notify(
            'typing-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('Invalid typing payload'))
            )
    
    fro = data.get('fro', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager

    """ in typing, `fro` should be the typer. the other person should be notified"""

    if data.get('fro') and connection_manager.connected_user(request.sid) and\
        data.get('fro') != connection_manager.connected_user(request.sid):
        return connection_manager.notify(
            'typing-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('payload typing user is different from connected user'))
            )

    if not User.user_exists(fro) and not User.user_exists(data.to):
        return connection_manager.notify(
            'typing-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('Invalid user-ids in typing payload'))
            )

    if connection_manager.is_connected(connection_manager.get_socket(data.get('to'))):
        """ create event to inform clients connected """
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.get_socket(data.get('to')), 
            json.dumps({'message': 'online.' })
        )
    else:
        print(f"typing-event-response: {data}")
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.connected_socket, 
            json.dumps({'message': 'away or offline' })
        )

@socketio.on('save-chat-request', namespace='/chat')
#@limiter.limit("1 per second")
def save(data):

    #return data
    print(f"Received 'save-chat-request' event {data}")

    event_schema = event_schemas.get('save-chat-request')
    fro = data.get('fro', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager
   
    if not jsonschema.validate(data, event_schema):
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('invalid save-chat-request payload'))
            )

    if data.get('fro') and connection_manager.connected_user(request.sid) and\
        data.get('fro') != connection_manager.connected_user(request.sid):
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('payload user is different from connected user'))
            )

    if not User.user_exists(fro) and not User.user_exists(data.to):
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('Invalid user-ids'))
            )
    
    chat = Chat()
    chat.from_dict(data, new_chat=True)
    db.session.add(chat)
    db.session.commit()
    response = chat.to_dict()
    #return response

    #if .to is online, tell .fro they're online
    if connection_manager.is_connected(connection_manager.get_socket(data.get('to'))):
        
        print(f"Finished processing 'save-chat-request' event: {response}")

        """ create event to inform clients connected """
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.get_socket(data.get('to')), 
            json.dumps({'message': response })
        )
    else:
        print(f"typing-event-response: {data}. But {data.get('to')} is offline now.")
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.connected_socket, 
            json.dumps({'message': 'away or offline' })
        )

@socketio.on('fetch-chat-request', namespace='/chat')
#@token_auth.login_required
def fetch(data):
    event_schema = event_schemas.get('fetch-chat-request')
    user_id = data.get('user-id', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager
    
    if not jsonschema.validate(data, event_schema):
        return connection_manager.notify(
            'fetch-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('Invalid Payload'))
            )
    
    if data.get('user-id') and connection_manager.connected_user(request.sid) and\
        data.get('user-id') != connection_manager.connected_user(request.sid):
        return connection_manager.notify(
            'fetch-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('payload user is different from connected user'))
            )

    if not User.user_exists(user_id):
        return connection_manager.notify(
            'fetch-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('invalid user-id'))
            )

    chat = Chat.query.filter(or_(Chat.to == user_id, Chat.fro == user_id)).order_by(Chat.updated.desc())
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Chat.to_collection_dict(chat, page, per_page, 'chat_api.get_chat', id=user_id)
    
    #connection_manager.notify(data.fro, json.dumps(data))
    return connection_manager.notify(
        'fetch-chat-response',
        connection_manager.connected_socket, 
        json.dumps({'message': data })
    )

@socketio.on('remove-chat-request', namespace='chat')
def remove(data):  # Use 'id' as the parameter name
    """ user-id & chat-id expected in the payload """
    event_schema = event_schemas.get('remove-chat-request')
    user_id = data.get('user-id', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager
    
    if not jsonschema.validate(data, event_schema):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('Invalid Payload'))
            )
    
    if data.get('user-id') and connection_manager.connected_user(request.sid) and\
        data.get('user-id') != connection_manager.connected_user(request.sid):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('payload user is different from connected user'))
            )

    if not User.user_exists(user_id):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('invalid user-id'))
            )

    chat = Chat.query.get(data['chat-id'])  # Replace 'chat_id' with 'id'
    if not chat:
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('invalid removed chat request, chat not found'))
            )
    
    if not (chat.fro == user_id or chat.to == user_id):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('invalid remove chat request, not the right user. '))
            )
        
    if chat.fro == user_id:
        chat.fro_del = True
    else:
        chat.to_del = True
    db.session.commit()  # Commit the session once

    return connection_manager.notify(
        'remove-chat-response',
        connection_manager.connected_socket, 
        json.dumps({'message': 'success! chat removed for you'})
    )
    
@socketio.on('update-chat-request')
def update(data):
    event_schema = event_schemas.get('update-chat-request')
    user_id = data.get('user-id', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager
    
    if not jsonschema.validate(data, event_schema):
        return connection_manager.notify(
            'update-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('invalid update Payload'))
            )

    if data.get('user-id') and connection_manager.connected_user(request.sid) and\
        data.get('user-id') != connection_manager.connected_user(request.sid):
        return connection_manager.notify(
            'update-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('update payload user is different from connected user'))
            )

    if not User.user_exists(user_id):
        return connection_manager.notify(
            'update-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('invalid update user-id'))
            )
    
    chat = Chat.chat_exists(data['chat-id']) #it returns chat object if exists and None otherwise
    if not chat:
        return connection_manager.notify( 
            'update-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('invalid update chat-id'))
            )
    
    if not chat.fro == user_id:
        return connection_manager.notify( 
            'update-chat-response',
            connection_manager.connected_socket, 
            json.dumps(bad_request('invalid update chat user-id'))
            )

    chat.from_dict(data, new_chat=False)
    db.session.commit()
    data = chat.to_dict()

    return connection_manager.notify(
        'update-chat-response',
        connection_manager.connected_socket, 
        json.dumps({'message': data})
    )

