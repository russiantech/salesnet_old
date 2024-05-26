import traceback
import jsonschema, json
from flask import Blueprint, request, jsonify
from flask_login import current_user
from web.utils.decorators import db_session_management
from web.models import db, Chat, User
from sqlalchemy import func, or_, and_
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
        "type": "string",
        "required": ["username"] #bcos it can also be gotten from socket-connections mapped
        },

    'remove-chat-request': {
        "type": "object",
        "properties": {
            "chat-id": {"type": "integer" },
            "user": {"type": "integer" }
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
    """ 
    Pls dont remove this comment: What I've noticed is we socket is that, on each request, the sid changes so you don't rely on the previous connected sid.
    Always work with current sid per request and maybe keep updating instead bcos it will always change and the current one is what's activate and where user can get response
    from when they make a request.
    """
    def connect(self, username, socket_id):
        """ only one connection is maintained for each user 
        """
        username = str(username) or str(current_user.username) if current_user.is_authenticated else str(True) #bcos redis does not allow None types or 0 or ''
        if self.get_socket(username) is not None:
            for k in self.get_active_connections().keys():
                if username is not None and str(k) == str(username):  # Check if v,username is not None before converting to int to avoid none type error.
                    print(f"Your-connected: {k}")
                    #self.disconnect(k)
                    #print(f"self-socket-> {self.get_socket(username)}")
                    return redis.hset('active_connections', k, socket_id ) #update instead
                
        return redis.hset('active_connections', username, socket_id) #set new-default
    
    def disconnect(self, sid):
        # Remove the entry for the disconnected sid
        for key, value in redis.hgetall('active_connections').items():
            if value == sid:
                print('deleting/disconnecting->', value)
                return redis.hdel('active_connections', key)

    def is_connected(self, dt):
        # Check if the username exists as a value in the hash 
        for v in self.get_active_connections().values():
            #print(v, dt)
            if dt is not None and str(dt).encode('utf-8') == v: 
                return True
        return False  # Return False if no match is found
    
    def is_connected1(self, dt):
        # Check if the username exists as a key/value in the hash 
        for k, v in self.get_active_connections().items():
            print(f"\n")
            print(f"{k, v, dt} \n")
            if dt is not None:
                dt =  str(dt).encode('utf-8') 
                if dt == k or dt == v: 
                    print(True)
                    return True
        return False  # Return False if no match is found

    def get_active_connections(self):
        # redis hgetall() command to retrieve all active connections from the hash
        connections = redis.hgetall('active_connections')
        return connections
    
    def remove_active_connections(self):
        #return redis.hdel('active_connections') #//cannot delete the entire hash
        return redis.delete('active_connections')
    
    def get_socket(self, username):
        """ Get socket_id based on username provided """
        for k, v in self.get_active_connections().items():
            #print(k, v, username)
            if username is not None \
                and k == str(username).encode('utf-8'):  # Check if k,username is not None before converting to str to avoid none type error. 
                #return v   # Return the socket ID if a match is found 
                socket = v.decode('utf-8') if isinstance(v, bytes) else v
                return socket   # Return the socket ID if a match is found 
        return None  # Return None if no match is found

    def get_username(self, socket_id):
        """ Get username based socket_id on  provided """
        for k, v in self.get_active_connections().items():
            #print(k, v, str(socket_id).encode('utf-8'))
            if v is not None and socket_id is not None and v == str(socket_id).encode('utf-8'):  # Check if k,username is not None before converting to str to avoid none type error.
                return str(k)  # Return the username(key) if a match is found 
        return None  # Return None if no match is found

    #socket-user-making-request at the moment
    def current_socket_id(self):
        return request.sid
    
    def notify(self, response_event, to_socket_id, msg):
        """
        This is used to notify/emit to both sides (sender and recipients)
        Args:
            to_socket_id: The recipient's socket ID. You can use get_socket() method of connection_manager(), provided a user-id, to get the recipient socket-id
            response_event: Specify the type of event you're responding to.
            msg: The response message.
        """
        fro_socket_id = self.current_socket_id()

        print(f"from-socket->{fro_socket_id}, to-socket->{to_socket_id}")

        rooms = [fro_socket_id]

        if to_socket_id is not None and (to_socket_id not in rooms and to_socket_id != fro_socket_id):
            rooms.append(to_socket_id)


        if self.is_connected(fro_socket_id) or self.is_connected(to_socket_id):
            print(f'all connected > {self.get_active_connections()}')
            print(f'sending-to > {rooms}')
            return socketio.emit(response_event, msg, room=rooms)
        else:
            print(f'rooms->{rooms}\n')
            print(f'{self.is_connected(fro_socket_id), self.is_connected(to_socket_id)}')
            print(f'{fro_socket_id, to_socket_id}')
      
connection_manager = ConnectionManager()

def handle_response(success, message, data=None, error_message=None):
    """ only success response should have data and be set to True. And  """
    response_data = {
        'server_sid': connection_manager.current_socket_id(), #const
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

@socketio.on('is_authenticated')
@limiter.limit("1 per second")
@db_session_management
def handle_auth_connect(username):
    sid = request.sid
    username = username or current_user.username if current_user.is_authenticated else str(True) #//ie get loggedin username or set it to True b/4 connecting
    if not connection_manager.get_socket(username):
        print(f'{username} is connected')
        connection_manager.get_socket(username)
        connection_manager.connect(username, sid)
    if not connection_manager.get_username(sid): #or not connection_manager.get_socket(username):
        """ do not connect same user more than once """
        connection_manager.connect(username, sid)

@socketio.on('is_anonymous')
@limiter.limit("1 per second")
@db_session_management
def handle_auth_disconnect(username):
    username = username or current_user.username if current_user.is_authenticated else str(True) 
    if connection_manager.get_socket(username):
        """ remove/disconnect if found"""
        connection_manager.disconnect(connection_manager.get_socket(username) )

@socketio.on('connect')
@limiter.limit("1 per second")
@db_session_management
def handle_connect(currentUsername):
    """ socket ids changes per request/reconnection, so ensure you reconnect everytime here."""
    sid = request.sid
    username = currentUsername or current_user.username if current_user.is_authenticated else str(True) #//ie get loggedin username or set it to True b/4 connecting
    connection_manager.connect(username, sid)
    print(connection_manager.get_active_connections())

@socketio.on('typing-request')
@db_session_management
def handle_typing(data):
    try:
        #schema = json.load(schema_file)
        print(f'typing data: {data}')
        event_schema = event_schemas.get('typing-request')
        data = json.loads(data, strict=False)

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
@db_session_management
def save(data):
    try:
        """ convert to dict - identify the corresponding schema - validate connected-user - check user existence - save chat - notify connected user(s) """
        data = json.loads(data) if data is not None else {} #without this, you get str object have no attr .get() cos `data` will be loaded as aa str
        event_schema = event_schemas.get('save-chat-request')
        #print(f'save-chat-request', data)
        #socketio.emit('save-chat-response', {"success": True, "message": "Test response"})
        jsonschema.validate(instance=data, schema=event_schema)

        fro_username = data.get('fro') or current_user.username if current_user.is_authenticated else None
        to_username = data.get('to')

        froexist = User.user_exists(fro_username)

        toexist = User.user_exists(to_username)
        #toexist = User.user_exists('edet')

        if not froexist or not toexist:
            return connection_manager.notify(
                'save-chat-response',
                connection_manager.current_socket_id(), 
                handle_response(False, None, error_message=f'save-chat-request failed for {fro_username}|{to_username}')
            )
        
        """ data['fro'] = froexist.id #?//still same thing though
        data['to'] = toexist.id """

        data.update( {'fro': froexist.id, 'to': toexist.id } )

        chat = Chat()
        chat.mark_recent(froexist.id, toexist.id) # invalidate old recent-chat, so that this newly inserted becomes only most recent
        chat.recent=True
        chat.from_dict(data, new_chat=True)
        db.session.add(chat)
        db.session.commit()
        db.session.flush()
        db.session.refresh(chat) 
        data = chat.to_dict()

        """ update some other data in the returned dict """
        fro_avatar_url = froexist.avatar(100) 

        data['fro_username'] = froexist.username
        data['fro_avatar'] = fro_avatar_url

        print(data)

        return connection_manager.notify(
            'save-chat-response',
            connection_manager.get_socket(to_username), 
            # If successful
            #handle_response(True, 'Request was processed successfully', 'Your data data here')
            #handle_response(True, 'save chat success', data = data, error_message=None)
            handle_response(True, '', data = data)
        )
    
    except jsonschema.exceptions.ValidationError as e:
        # Handle the validation error here
        return connection_manager.notify(
            'save-chat-response',
            connection_manager.current_socket_id(), 
            handle_response(False, 'Jsonschema.exceptions.ValidationError', error_message=str(e))
        )
    
    except Exception as e:
        # Print the traceback
        traceback.print_exc()
        return connection_manager.notify(
            'save-chat-response', 
            connection_manager.current_socket_id(), 
            handle_response(False, 'exception', error_message=str(e))
            )

@socketio.on('fetch-chat-request')
@limiter.limit("1 per second")
@db_session_management
def fetch(username):
    try:
        event_schema = event_schemas.get('fetch-chat-request')

        username = username or current_user.username if current_user.is_authenticated else username

        jsonschema.validate(username, event_schema)
        
        user = User.user_exists(username)

        if not user:

            response = handle_response(
                False,
                None,
                error_message=f"fetch-chat-request failed. Illegal( {username}) not recognized by chatme."
            )

            return connection_manager.notify('fetch-chat-response', connection_manager.current_socket_id(), response)
        
        """ working demo in russiant with recent set to True """
        chat1 = Chat.query.filter(
            and_(or_(Chat.fro == user.id, Chat.to == user.id), Chat.recent == True ) ).order_by(Chat.created.desc() ).all()
        
        user_a_chats = Chat.query.filter(Chat.participants.contains(user_a)).all()
        
        """ chat = Chat.query.filter(
            and_(or_(Chat.fro == user.id, Chat.to == user.id), Chat.recent == True)
              ).group_by(Chat.fro, Chat.to).order_by(Chat.created.desc() ).all() """
        
        chat = Chat.query.filter(
            or_(Chat.fro == user.id, Chat.to == user.id) ).group_by(Chat.fro, Chat.to).order_by(Chat.created.desc() ) #.all() #adding this will make the query object a list which cannot be paginated
        #from sqlalchemy.sql.expression import func
        if not chat.first():
            chat = (User.query.filter(User.id != current_user.id) # Exclude the current user
                .order_by(func.random())  # Randomize the order of users
                 #.all() #// remove this, to have an object instead of a list
            )
            
            #chat = db.session.query(User).filter(User.id != current_user.id).order_by(func.random()).limit(20)

        if chat.first():
            print([chat.id for chat in chat])

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        #data = Chat.to_collection_dict(chat, page, per_page, 'main.salespage', salespage=username)
        data = Chat.to_collection_dict(chat, page, per_page, 'main.userspage', userpage=username)

        response = handle_response(True, 'chat fetched', data=data)
        return connection_manager.notify('fetch-chat-response', connection_manager.get_socket(username), response)

    except jsonschema.exceptions.ValidationError as e:
        response = handle_response(False, None, error_message=str(e))
        return connection_manager.notify('fetch-chat-response', connection_manager.current_socket_id(), response)


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

