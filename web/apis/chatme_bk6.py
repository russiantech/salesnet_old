import traceback
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
            "to": { "type": "string" },
            "fro": { "type": "string" },
            "text": { "type": "string" },
            "sticker": { "type": "string" },
            "media": { "type": "string" }
        },
        "required": ["to", "fro"],
        "anyOf": [
            { 
            "required": ["text"],
            },
            { 
            "required": ["media"],
            },
            { 
            "required": ["sticker"],
            },
            { 
            "required": ["text", "sticker"]
            },
            {
            "required": ["text", "media"]
            },
            {
            "required": ["sticker", "media"]
            }
        ]
        },

    'fetch-chat-request': {
        "type": "object",
        "properties": {
            "username": { "type": "string" }
        },
        "required": ["username"] #bcos it can also be gotten from socket-connections mapped
        },

    'remove-chat-request': {
        "type": "object",
        "properties": {
            "chat-id": {"type": "integer" },
            "fro": {"type": "integer" }
        },
        "required": ["chat_id", "username"],
        },

    'update-chat-request': {
        "type": "object",
        "properties": {
            "fro": {"type": "integer" },
            "chat-id": {"type": "integer" },
            "chat-content": {"type": "string"}
        },
        "required": ["chat-id", "chat-content", "fro"]
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

    def connect1(self, socket_id, user_id):
        """ only one connection is maintained for each user 
        """
        user_id = current_user.id if current_user.is_authenticated else True #bcos redis does not allow None types or 0 or ''
        if self.get_socket(user_id) is not None:
            for k, v in self.get_active_connections().items():
                if v is not None and user_id is not None and int(v) == int(user_id):  # Check if v,user_id is not None before converting to int to avoid none type error.
                    print(f"Your connected sessions: {k}")
                    self.disconnect(k)
        redis.hset('active_connections', str(socket_id), int(user_id)) 

    def connect(self, socket_id, username):
        """ only one connection is maintained for each user 
        """
        username = str(username) or str(current_user.username) if current_user.is_authenticated else str(True) #bcos redis does not allow None types or 0 or ''
        if self.get_socket(username) is not None:
            for k in self.get_active_connections().keys():
                #if k is not None and username is not None and int(k) == int(username):  # Check if v,username is not None before converting to int to avoid none type error.
                if k is not None and username is not None and str(k) == str(username):  # Check if v,username is not None before converting to int to avoid none type error.
                    print(f"Your connected sessions: {k}")
                    #self.disconnect(k)
                    return redis.hset('active_connections', k, socket_id ) #update instead
                
        return redis.hset('active_connections', username, socket_id) #set new-default
    
    def disconnect(self, socket_id):
        return redis.hdel('active_connections', socket_id)

    def is_connected1(self, socket_id):
        # redis hexists() command to check if the socket_id exists in the hash
        return redis.hexists('active_connections', socket_id)
    
    def is_connected(self, dt):
        # Check if the username exists as a key or a value in the hash
        if redis.hexists('active_connections', str(dt).encode('utf-8') ) or \
            str(dt).encode('utf-8') in redis.hvals('active_connections'):
            return True
        return False
    
    def get_active_connections(self):
        # redis hgetall() command to retrieve all active connections from the hash
        connections = redis.hgetall('active_connections')
        return connections
    
    def remove_active_connections(self):
        #return redis.hdel('active_connections') #//cannot delete the entire hash
        return redis.delete('active_connections')
    
    def get_socket(self, username):
        """ Get socket_id based username on  provided """
        for k, v in self.get_active_connections().items():
            #print(k, v)
            #print(k, username)
            if k is not None and username is not None \
                and str(k).encode('utf-8') == str(username).encode('utf-8'):  # Check if k,username is not None before converting to str to avoid none type error.
                return str(v)  # Return the socket ID if a match is found 
        return None  # Return None if no match is found
    
    def get_username(self, socket_id):
        """ Get username based socket_id on  provided """
        for k, v in self.get_active_connections().items():
            #print(k, v)
            if v is not None and socket_id is not None and v == str(socket_id).encode('utf-8'):  # Check if k,username is not None before converting to str to avoid none type error.
                return str(k)  # Return the socket ID if a match is found 
        return None  # Return None if no match is found

    #socket-user-making-request at the moment
    def current_socket_id(self):
        return request.sid
    
    def notify(self, response_event, socket_id, msg):
        """ 
        This will be used to notify/emit to only sender. Typically where there's message processing issues.
        args:event, msg 
        """
        if not self.is_connected(self.current_socket_id()):
            print(self.get_active_connections())
            print(self.current_socket_id(), request.sid.encode('utf-8'))
            print(f"Not connected though, but will still send to {self.is_connected(self.current_socket_id()), '--', self.current_socket_id()}")
            
        #return socketio.emit(response_event, msg, room=socket_id)
        if self.is_connected(self.current_socket_id()):
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

@socketio.on('signedin')
@limiter.limit("1 per second")
@db_session_management
def handle_auth_connect(data):
    data = json.loads(data)
    sid = request.sid
    username = data.get('username', current_user.username if current_user.is_authenticated else True ) #//ie get loggedin username or set it to True b/4 connecting
    if not connection_manager.get_socket(username):
        print(f'{username} is connected')
        connection_manager.get_socket(username)
        connection_manager.connect(username, sid)
    if not connection_manager.get_username(sid): #or not connection_manager.get_socket(username):
        """ do not connect same user more than once """
        connection_manager.connect(username, sid)

@socketio.on('signedout')
@limiter.limit("1 per second")
@db_session_management
def handle_auth_disconnect(data):
    data = json.loads(data)
    #connection_manager.connect(request.sid, data.get('username'))
    if connection_manager.get_username(request.sid) or connection_manager.get_socket(data.get('username')):
        """ remove/disconnect """
        connection_manager.disconnect(connection_manager.get_socket(data.get('username')) )

@socketio.on('connected')
@limiter.limit("1 per second")
@db_session_management
def handle_connect(data):
    data = json.loads(data)
    sid = request.sid
    username = data.get('username', current_user.username if current_user.is_authenticated else True ) #//ie get loggedin username or set it to True b/4 connecting
    if not connection_manager.get_socket(username):
        print(f'{username} is connected')
        connection_manager.get_socket(username)
        connection_manager.connect(username, sid)
    if not connection_manager.get_username(sid): #or not connection_manager.get_socket(username):
        """ do not connect same user more than once """
        connection_manager.connect(username, sid)

    """ username = connection_manager.get_username(sid)
    user_id_from_socket_id = connection_manager.get_username(sid)
    socket_id_from_user_id = connection_manager.get_socket(user_id_from_socket_id) 
    
    print(f"get_active_connections: {connection_manager.get_active_connections()}")
    print(f"current_socket:{connection_manager.current_socket_id()}")
    print(f"username:{username}")
    print(f"socket_id_from_user_id:{socket_id_from_user_id}")
    print(f"user_id_from_socket_id:{user_id_from_socket_id}") """

@socketio.on('disconnected')
@limiter.limit("1 per second")
@db_session_management
def handle_disconnect():
    sid = request.sid
    if connection_manager.is_connected(connection_manager.current_socket_id()):
        connection_manager.disconnect(connection_manager.current_socket_id()) 
    connection_manager.disconnect(sid)
    print(f"Disconnected:- sid-{sid} : uid:- {connection_manager.get_username(sid)}")

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
        
        fro = data.get('fro', connection_manager.get_username(request.sid)) #get sender from payload or connection-manager

        """ in typing, `fro` should be the typer. the other person should be notified"""

        if data.get('fro') and connection_manager.get_username(request.sid) and\
            data.get('fro') != connection_manager.get_username(request.sid):
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
        """ convert to dict - identify the corresponding schema - validate connected-user - check user existnce - save chat - notify connected user(s) """
        data = json.loads(data) #without this, you get str object have no attr .get() cos `data` will be loaded as aa str
        event_schema = event_schemas.get('save-chat-request')
        
        #socketio.emit('save-chat-response', {"success": True, "message": "Test response"})
        jsonschema.validate(instance=data, schema=event_schema)

        if data.get('fro') is not None and connection_manager.get_username(request.sid) is not None \
            and str(data.get('fro')) != str(connection_manager.get_username(request.sid)):
            #print(f"payload-user:{data.get('fro')}, connected-user:{connection_manager.get_username(request.sid)}")
            return connection_manager.notify(
                'save-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(False, None, 
                                error_message=f"{data.get('text')}, \n payload user is different from connected user")
            )

        fro = data.get('fro', connection_manager.get_username(request.sid)) #get sender from payload or connection-manager
        
        froexist = User.user_exists(fro)
        toexist = User.user_exists(data.get('to'))

        #print(froexist)
        
        if not froexist and not toexist :
            return connection_manager.notify(
                'save-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(False, None, error_message='Invalid save-chat-request user-names')
            )
        
        """ data['fro'] = froexist.id #?//still same thing though
        data['to'] = toexist.id """

        data.update(
            {'fro': froexist.id, 'to': toexist.id }
            )

        chat = Chat()
        chat.from_dict(data, new_chat=True)
        db.session.add(chat)
        db.session.commit()
        db.session.flush()
        db.session.refresh(chat) 
        response = chat.to_dict()

        """ update some other data in the returned dict """
        response['fro_username'] = froexist.username
        response['fro_image'] = froexist.image
        #response['to_image'] = toexist.image
        #return response

        #if .to is online, tell .fro they're online
        if connection_manager.is_connected(connection_manager.get_socket(response.get('to'))):
            """ create event to inform clients connected """
            return connection_manager.notify_us(
                'save-chat-response',
                connection_manager.get_socket(response.get('to')), 
                # If successful
                #handle_response(True, 'Request was processed successfully', 'Your response data here')
                handle_response(True, 'save chat success', data = response)
            )
        else:
            #print(f"save-chat-response: {data}. But {data.get('to')} is offline now.")
            return connection_manager.notify(
                'save-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(True, 'Request was processed successfully', data = response )
            )
    
    except jsonschema.exceptions.ValidationError as e:
        # Handle the validation error here
        #print(handle_response(False, f'As jsonschema.exceptions.ValidationError on: {data} ', error_message=str(e)))
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.current_socket_id(), 
            handle_response(False, 'Jsonschema.exceptions.ValidationError', error_message=str(e))
        )
    
    except Exception as e:
        # Print the traceback
        #traceback.print_exc()
        print(handle_response(False, 'Exception happened', error_message=str(Exception)))
        return connection_manager.notify(
                'save-chat-response', 
                connection_manager.current_socket_id(), 
                handle_response(False, 'Exception', error_message=str(e))
                )

@socketio.on('fetch-chat-request')
@limiter.limit("1 per second")
@db_session_management
def fetch(data):
    try:
        event_schema = event_schemas.get('fetch-chat-request')

        jsonschema.validate(data, event_schema)
        
        if data.get('username') and connection_manager.get_username(request.sid) and\
            data.get('username') != connection_manager.get_username(request.sid):
            return connection_manager.notify(
                'fetch-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(
                    False, 'connected user validation error', 
                    error_message=f"{data.get('username')}, \n Fetch-chat-request failed. Payload user is different from socket user")
            )
        
        username = data.get('username', connection_manager.get_username(request.sid)) #get sender from payload or connection-manager

        user = User.user_exists(username)

        if not user:
            return connection_manager.notify(
                'fetch-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(
                    False, None, 
                    error_message=f"Fetch-chat-request failed for {username}. They're not recognized by chatme. ")
            )

        #chat = Chat.query.filter(or_(Chat.to == username, Chat.fro == username)).order_by(Chat.updated.desc())
        chat = Chat.query.filter(or_(Chat.to == user.id, Chat.fro == user.id)).order_by(Chat.updated.desc())
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        data = Chat.to_collection_dict(chat, page, per_page, 'chat_api.get_chat', id=username)
        
        #connection_manager.notify(data.fro, json.dumps(data))
        return connection_manager.notify(
            'fetch-chat-response',
            connection_manager.get_socket(username), 
            # If successful
            #handle_response(True, 'Request was processed successfully', 'Your response data here')
            handle_response(True, 'save chat success',  data=data)
        )
    
    #except Exception as e:
    except jsonschema.exceptions.ValidationError as e:
    # Handle the validation error here
        #return handle_response(False, 'An error occurred', error_message=str(e))
        print(f"{connection_manager.current_socket_id()}")
        return connection_manager.notify(
            'fetch-chat-response',
            connection_manager.current_socket_id(), 
            handle_response(False, None, error_message=str(e))
        )


@socketio.on('remove-chat-request', namespace='chat')
@limiter.limit("1 per second")
@db_session_management
def remove(data):  # Use 'id' as the parameter name
    """ user-id & chat-id expected in the payload """
    event_schema = event_schemas.get('remove-chat-request')
    username = data.get('user-id', connection_manager.get_username(request.sid)) #get sender from payload or connection-manager
    
    if not jsonschema.validate(data, event_schema):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('Invalid Payload'))
            )
    
    if data.get('user-id') and connection_manager.get_username(request.sid) and\
        data.get('user-id') != connection_manager.get_username(request.sid):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('payload user is different from connected user'))
            )

    if not User.user_exists(username):
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
    
    if not (chat.fro == username or chat.to == username):
        return connection_manager.notify(
            'remove-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid remove chat request, not the right user. '))
            )
        
    if chat.fro == username:
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
    username = data.get('fro', connection_manager.get_username(request.sid)) #get sender from payload or connection-manager
    
    if not jsonschema.validate(data, event_schema):
        return connection_manager.notify(
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid update Payload'))
            )

    if data.get('fro') and connection_manager.get_username(request.sid) and\
        data.get('fro') != connection_manager.get_username(request.sid):
        return connection_manager.notify(
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('update payload user is different from connected user'))
            )

    if not User.user_exists(username):
        return connection_manager.notify(
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid update fro'))
            )
    
    chat = Chat.chat_exists(data['chat-id']) #it returns chat object if exists and None otherwise
    if not chat:
        return connection_manager.notify( 
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid update chat-id'))
            )
    
    if not chat.fro == username:
        return connection_manager.notify( 
            'update-chat-response',
            connection_manager.current_socket_id(), 
            jsonify(bad_request('invalid update chat fro'))
            )

    chat.from_dict(data, new_chat=False)
    db.session.commit()
    data = chat.to_dict()

    return connection_manager.notify(
        'update-chat-response',
        connection_manager.current_socket_id(), 
        json.dumps({'message': data})
    )

