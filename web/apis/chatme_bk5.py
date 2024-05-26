import jsonschema, json

from flask import Blueprint, request, jsonify
from flask_login import current_user
from web.utils.decorators import db_session_management
from web.models import db, Chat, User
from sqlalchemy import or_
from web.extensions import socketio, limiter, redis
#from web.apis.errors import bad_request
#from web.apis.tokens import hash_auth

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
            "fro": { "type": "integer" }
        },
        #"required": ["user-id"] #bcos it can also be gotten from socket-connections mapped
        },

    'remove-chat-request': {
        "type": "object",
        "properties": {
            "chat-id": {"type": "integer" },
            "fro": {"type": "integer" }
        },
        "required": ["chat-id", "user-id"]
        },

    'update-chat-request': {
        "type": "object",
        "properties": {
            "fro": {"type": "integer" },
            "chat-id": {"type": "integer" },
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
        #return redis.hset('active_connections', str(socket_id), hash_auth.hash_id(str(user_id)) )
        #return redis.hset('active_connections', str(socket_id), int(user_id)) 
        #if self.is_connected(socket_id): 
        #print(f'{self.is_connected(socket_id)} self is connected already though')
        #print(f'{self.get_socket(user_id)} socket connected already though')
        #if not self.is_connected(socket_id) or not self.get_socket(user_id):
        #if not self.get_socket(user_id):
        """ if passed socket_id and user_id is'nt connected already"""
        #redis.hset('active_connections', str(socket_id), int(user_id)) 
        if self.get_socket(user_id) is not None:
            for k, v in self.get_active_connections().items():
                if v is not None and user_id is not None and int(v) == int(user_id):  # Check if v,user_id is not None before converting to int to avoid none type error.
                    print(f"Your connected sessions: {k}")
                    self.disconnect(k)

                redis.hset('active_connections', str(socket_id), int(user_id)) 
    
    def connect1(self, socket_id):
        user_id = current_user.id if current_user.is_authenticated else True
        if user_id:
            existing_socket_id = self.get_socket(user_id)
            if existing_socket_id:
                # Update the existing connection with the new socket ID
                #redis.hset('active_connections', str(existing_socket_id), None)
                redis.hdel('active_connections', existing_socket_id)

            
            # Create a new connection or update the existing one
            redis.hset('active_connections', str(socket_id), int(user_id))


    def disconnect(self, socket_id):
        # Use the Redis HDEL command to remove the connection from the hash
        #return redis.hdel('active_connections', str(socket_id))
        #redis.hdel('active_connections', str(socket_id))
        redis.hdel('active_connections', socket_id)

    def is_connected(self, socket_id):
        # Use the Redis HEXISTS command to check if the socket_id exists in the hash
        return redis.hexists('active_connections', str(socket_id))
    
    def get_active_connections(self):
        # Use the Redis HGETALL command to retrieve all active connections from the hash
        connections = redis.hgetall('active_connections')
        #print(f"active-connections: {connections}")
        return connections
    
    def remove_active_connections(self):
        #return redis.hdel('active_connections') #//cannot delete the entire hash
        return redis.delete('active_connections')
    
    def get_socket(self, uid):
        """ Get socket-id based on user-id provided """
        for k, v in self.get_active_connections().items():
            print(f"{k}------{v}\n")
            #if all(v is not None, uid is not None) and int(v) == int(uid):  # Check if v,uid is not None before converting to int to avoid none type error.
            if v is not None and uid is not None and int(v) == int(uid):  # Check if v,uid is not None before converting to int to avoid none type error.
                return str(k)  # Return the socket ID if a match is found 
        return None  # Return None if no match is found

    
    def connected_user(self, socket_id):
        # Use the Redis HGET command to get the user ID associated with the socket ID
        """ Will get connected socket user-d based on connected socket sid  """
        user_id = redis.hget('active_connections', str(socket_id))
        if user_id is not None:
            return int(user_id)
        else:
            # Handle the case where no user is found for the given socket ID
            return None

    #socket-user-making-request at the moment
    def current_socket_id(self):
        return str(request.sid)
    
    def notify(self, response_event, socket_id, msg):
        """ 
        This will be used to notify/emit to only sender. Typically where there's message processing issues.
        args:event, msg 
        """
        if self.is_connected(socket_id):
            print(f'notifyer says connected: {msg}')
            #socketio.emit(response_event, msg, room=socket_id)
            return socketio.emit(response_event, msg, room=socket_id)
    
    def notify_us(self, response_event, to_socket_id, msg):
        """
        This is used to notify/emit to both sides(sender n recipients)
        Args: 
            to_socket_id: The recipient's socket ID. You can use get_socket() method of connection_manager(), provided a user-id, to get the recipient socket-id
            response_event: Specify the type of event you're responding to.
            msg: The response message.
        """
        fro_socket = self.current_socket_id()
        rooms = [fro_socket, to_socket_id]  # Include both sender and recipient socket IDs
        if self.is_connected(fro_socket) or self.is_connected(to_socket_id):
            print(f'Notifier is sending the message: {msg}')
            socketio.emit(response_event, msg, room=rooms)
        else:
            print(f'Neither sender nor recipient is connected. Message not sent.')
      
connection_manager = ConnectionManager()

def handle_response(success, message, data=None, error_message=None):
    """ only success response should have data and be set to True. And  """
    response_data = {
        'server_sid': connection_manager.current_socket_id(),
        'success': success,
        'message': message,
    }
    if data:
        response_data['data'] = data
    if error_message:
        response_data['error_message'] = error_message

    return response_data

def bad_request(error_msg):
    response = {
        'error': True,
        'response':f"{error_msg}"
    }
    return jsonify(response)

@socketio.on('connected')
@limiter.limit("1 per second")
@db_session_management
def handle_connect(data):
    data = json.loads(data)
    fro = data.get('fro', connection_manager.connected_user(request.sid))
    #connection_manager.remove_active_connections()
    #print(data)
    print(f"get_active_connections: {connection_manager.get_active_connections()}")
    sid = request.sid
     
    if connection_manager.get_socket(fro):
        print('yes - they are connected')
    if not connection_manager.connected_user(sid) or not connection_manager.get_socket(fro):
        """ do not connect same user more than once """
        connection_manager.connect(sid)
    print(f"socket-id: {sid} : user-id: {connection_manager.connected_user(sid)}, \
           socket-id from user-id:{connection_manager.get_socket(1) },\
           user-id from socket-id:{connection_manager.connected_user(sid) }")

@socketio.on('disconnected')
@limiter.limit("1 per second")
@db_session_management
def handle_disconnect():
    sid = request.sid
    connection_manager.disconnect(sid)
    print(f"Disconnected:- sid-{sid} : uid:- {connection_manager.connected_user(sid)}")

@socketio.on('typing-request')
@db_session_management
def handle_typing(data):
    try:
        #schema = json.load(schema_file)
        print(f'typing data: {data}')
        event_schema = event_schemas.get('typing-request')
        #data = json.load(data)
        #data = json.loads(request.data, strict=False)
        data = json.loads(data, strict=False)
        #data['to'] = hash_auth.unhash(data.get('to'))
        #data['fro'] = hash_auth.unhash(data.get('fro'))
        if not jsonschema.validate(data, event_schema):
            return connection_manager.notify(
                'typing-response', 
                connection_manager.current_socket_id(), 
                bad_request('Invalid typing payload')
                )
        
        fro = data.get('fro', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager

        """ in typing, `fro` should be the typer. the other person should be notified"""

        if data.get('fro') and connection_manager.connected_user(request.sid) and\
            data.get('fro') != connection_manager.connected_user(request.sid):
            return connection_manager.notify(
                'typing-response',
                connection_manager.current_socket_id(), 
                jsonify(bad_request('payload typing user is different from connected user'))
                )

        if not User.user_exists(fro) and not User.user_exists(data.to):
            return connection_manager.notify(
                'typing-response',
                connection_manager.current_socket_id(), 
                jsonify(bad_request('Invalid user-ids in typing payload'))
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
                connection_manager.current_socket_id(), 
                json.dumps({'message': 'away or offline' })
            )
    except Exception as e:
        print(e)
        return connection_manager.notify(
                'typing-response', 
                connection_manager.current_socket_id(), 
                bad_request(f'issues: {e}')
                )

@socketio.on('save-chat-request')
@limiter.limit("1 per second")
#@db_session_management
def save(data):

    try:
        data = json.loads(data) #without this, you get str object have no attr .get() cos `data` will be loaded as aa str
        event_schema = event_schemas.get('save-chat-request')
        
        """#if not jsonschema.validate(data, event_schema):
        if not jsonschema.validate(instance=data, schema=event_schema):
            return connection_manager.notify(
                'save-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(False, 'Schema Validation Error', error_message='Invalid save-chat-request payload')
            ) """
        
        #if all((data.get('fro') is not None, connection_manager.connected_user(request.sid) is not None)) \
        if data.get('fro') is not None and connection_manager.connected_user(request.sid) is not None \
            and int(data.get('fro')) != int(connection_manager.connected_user(request.sid)):
            print('--------------------')
            return connection_manager.notify(
                'save-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(False, 'connected user validation error', 
                                error_message=f"{data.get('text')}, \n payload user is different from connected user")
            )


        fro = data.get('fro', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager
        if not User.user_exist(fro) and not User.user_exist(data.get('to') ):
            return connection_manager.notify(
                'save-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(False, 'user(s) not found error', error_message='Invalid save-chat-request user-ids')
            )

        chat = Chat()
        chat.from_dict(data, new_chat=True)
        db.session.add(chat)
        db.session.commit()
        response = chat.to_dict()
        #return response

        #if .to is online, tell .fro they're online
        if connection_manager.is_connected(connection_manager.get_socket(data.get('to'))):
            """ create event to inform clients connected """
            return connection_manager.notify_us(
                'save-chat-response',
                connection_manager.get_socket(data.get('to')), 
                # If successful
                #handle_response(True, 'Request was processed successfully', 'Your response data here')
                handle_response(True, 'Request was processed successfully', response )
            )
        else:
            print(f"save-chat-response: {data}. But {data.get('to')} is offline now.")
            return connection_manager.notify(
                'save-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(True, 'Request was processed successfully', response )
            )
    
    except jsonschema.exceptions.ValidationError as e:
        # Handle the validation error here
        print(handle_response(False, 'As jsonschema.exceptions.ValidationError', error_message=str(e)))
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.current_socket_id(), 
            handle_response(False, 'jsonschema.exceptions.ValidationError', error_message=str(e))
        )
    
    except Exception as e:
        print(handle_response(False, 'Exception occured', error_message=str(e)))
        return connection_manager.notify(
                'save-chat-response', 
                connection_manager.current_socket_id(), 
                handle_response(False, 'As gen exception', error_message=str(e))
                )

@socketio.on('fetch-chat-request')
@limiter.limit("1 per second")
@db_session_management
def fetch(data):
    try:
        event_schema = event_schemas.get('fetch-chat-request')

        """ if not jsonschema.validate(data, event_schema):
            return connection_manager.notify(
                'fetch-chat-response',
                connection_manager.current_socket_id(), 
                jsonify(bad_request('Invalid Payload'))
                ) """

        jsonschema.validate(data, event_schema)

        user_id = data.get('user-id', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager
        
        if data.get('user-id') and connection_manager.connected_user(request.sid) and\
            data.get('user-id') != connection_manager.connected_user(request.sid):
            return connection_manager.notify(
                'fetch-chat-response',
                connection_manager.current_socket_id(), 
                jsonify(bad_request('payload user is different from connected user'))
                )

        if not User.user_exists(user_id):
            return connection_manager.notify(
                'fetch-chat-response',
                connection_manager.current_socket_id(), 
                jsonify(bad_request('invalid/unknown user-id'))
                )

        chat = Chat.query.filter(or_(Chat.to == user_id, Chat.fro == user_id)).order_by(Chat.updated.desc())
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        data = Chat.to_collection_dict(chat, page, per_page, 'chat_api.get_chat', id=user_id)
        
        #connection_manager.notify(data.fro, json.dumps(data))
        return connection_manager.notify(
            'fetch-chat-response',
            connection_manager.current_socket_id(), 
            json.dumps({'message': data })
        )
    
    #except Exception as e:
    except jsonschema.exceptions.ValidationError as e:
    # Handle the validation error here
        #return handle_response(False, 'An error occurred', error_message=str(e))
        return connection_manager.notify(
            'fetch-chat-response',
            connection_manager.current_socket_id(), 
            handle_response(False, 'An error occurred', error_message=str(e))
        )


@socketio.on('remove-chat-request', namespace='chat')
@limiter.limit("1 per second")
@db_session_management
def remove(data):  # Use 'id' as the parameter name
    """ user-id & chat-id expected in the payload """
    event_schema = event_schemas.get('remove-chat-request')
    user_id = data.get('user-id', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager
    
    if not jsonschema.validate(data, event_schema):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('Invalid Payload'))
            )
    
    if data.get('user-id') and connection_manager.connected_user(request.sid) and\
        data.get('user-id') != connection_manager.connected_user(request.sid):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('payload user is different from connected user'))
            )

    if not User.user_exists(user_id):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid user-id'))
            )

    chat = Chat.query.get(data['chat-id'])  # Replace 'chat_id' with 'id'
    if not chat:
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid removed chat request, chat not found'))
            )
    
    if not (chat.fro == user_id or chat.to == user_id):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid remove chat request, not the right user. '))
            )
        
    if chat.fro == user_id:
        chat.fro_del = True
    else:
        chat.to_del = True
    db.session.commit()  # Commit the session once

    return connection_manager.notify(
        'remove-chat-response',
        connection_manager.current_socket_id(), 
        json.dumps({'message': 'success! chat removed for you'})
    )
    
@socketio.on('update-chat-request')
@limiter.limit("1 per second")
@db_session_management
def update(data):
    event_schema = event_schemas.get('update-chat-request')
    user_id = data.get('user-id', connection_manager.connected_user(request.sid)) #get sender from payload or connection-manager
    
    if not jsonschema.validate(data, event_schema):
        return connection_manager.notify(
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid update Payload'))
            )

    if data.get('user-id') and connection_manager.connected_user(request.sid) and\
        data.get('user-id') != connection_manager.connected_user(request.sid):
        return connection_manager.notify(
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('update payload user is different from connected user'))
            )

    if not User.user_exists(user_id):
        return connection_manager.notify(
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid update user-id'))
            )
    
    chat = Chat.chat_exists(data['chat-id']) #it returns chat object if exists and None otherwise
    if not chat:
        return connection_manager.notify( 
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid update chat-id'))
            )
    
    if not chat.fro == user_id:
        return connection_manager.notify( 
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid update chat user-id'))
            )

    chat.from_dict(data, new_chat=False)
    db.session.commit()
    data = chat.to_dict()

    return connection_manager.notify(
        'update-chat-response',
        connection_manager.current_socket_id(), 
        json.dumps({'message': data})
    )

