from flask import Blueprint, jsonify, request, url_for
from flask_login import current_user
from web.models import db, Chat, User
from sqlalchemy import or_
from  web.extensions import socketio
from web.apis.errors import bad_request, response

chat_api = Blueprint('chat_api', __name__)

# // General/(*) chat/conversations
import uuid, json
# Assuming that socketio is your SocketIO instance

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    def connect(self, socket_id):
        self.active_connections[socket_id] = True

    def disconnect(self, socket_id):
        if socket_id in self.active_connections:
            del self.active_connections[socket_id]

    def is_connected(self, socket_id):
        return socket_id in self.active_connections

    def send_chat_to(self, socket_id, message):
        if self.is_connected(socket_id):
            socketio.emit('chat', message, room=socket_id)

connection_manager = ConnectionManager()

payload = {
    'to' : 0,
    'fro' : 0,
    'text' : '',
    'sticker' : '',
    'media' : '',
    'client': False,
    "type": "connect", 
    #"id": user_id
    }

@socketio.on('connect')
def handle_connect():
    user_id = request.sid
    connection_manager.connect(user_id)
    connection_manager.send_chat_to(user_id, json.dumps(payload))

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    connection_manager.disconnect(user_id)

@socketio.on('typing')
def handle_typing(data):

    fro = request.sid or data['fro']
    to = data['to']
    txt = data['text']

    if connection_manager.is_connected(to):
        """ create event to inform clients connected """
        payload = {"type": "typing", "fro": fro, "text": txt}
        connection_manager.send_chat_to(to, json.dumps(payload))
    else:
        """pass"""
        print('recipient not connected')
        # Handle the case when the recipient is not connected
        # You can notify the sender or take other appropriate actions
    print('data is:', data)

@socketio.on('chat')
def handle_chat(data):
    fro = request.sid or  data['fro']
    to = data['to']
    message = data['text']
    
    if connection_manager.is_connected(to):
        """validate, save in db. create event to inform clients connected """
        connection_manager.send_chat_to(to, json.dumps({"type": "chat_message", "fro": fro, "message": message}))
    else:
        print('recipient not connected')
        # Handle the case when the recipient is not connected
        # You can notify the sender or take other appropriate actions
    print('Dt:', data)


""" class ConnectionManager_:
    def __init__(self):
        self.active_connections = {}

    def connect(self, socket):
        # inform * when a client connects
        id = str(uuid.uuid4())
        self.active_connections[id] = socket
        self.send_message_to(socket, json.dumps({"type": "connect", "id": id}))

    def disconnect(self, socket):
        id = self.find_connection_id(socket)
        del self.active_connections[id]
        return id

    def find_connection_id(self, socket):
        #find a specific connected user by connection-id
        return next((id for id, s in self.active_connections.items() if s == socket), None)

    def send_message_to(self, socket, message):
        #send to specify users connected 
        print(socket)
        socket.emit('message', message)

    def broadcast(self, message):
        #sending to all connected clients/users 
        for connection in self.active_connections.values():
            self.send_message_to(connection, message)

connection_manager = ConnectionManager()
 """

@chat_api.route('/chat', methods=['POST'])
def save_chat():
    data = request.get_json() or {}
    
    fro = data.get('fro')
    to = data.get('to')

    if not (['fro','to'] and ('text' or 'sticker' or 'media') ) in data:
        return bad_request('Can Not Send Blank Chats')

    if not User.user_exists(fro) and not User.user_exists(to):
        return bad_request('Invalid User Id(s)')
    
    chat = Chat()
    chat.from_dict(data, new_chat=True)
    db.session.add(chat)
    db.session.commit()
    response = jsonify(chat.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('chat_api.get_chat', id=chat.id)
    return response

""" @socketio.on('connect')
def handle_connect():
    connection_manager.connect(request.sid)
    #connect = connection_manager.connect(request.sid)
    print(f"User {'handle_connect'} Connected")

@socketio.on('disconnect')
def handle_disconnect():
    id = connection_manager.disconnect(request.sid)
    print(f"User {id} Disconnected")

@socketio.on('message')
def handle_message(data):
    id = connection_manager.find_connection_id(request.sid)
    print(f"Received message from User {id}: {data}")
    connection_manager.send_message_to(data)

@socketio.on('message_all')
def handle_message(data):
    id = connection_manager.find_connection_id(request.sid)
    print(f"Received message from User {id}: {data}")
    connection_manager.broadcast(data) """

#here, id is user_id
""" @chat_api.route('/chat/<int:user_id>', methods=['GET'])
#@token_auth.login_required
def get_chat(user_id):
    if current_user.is_authenticated and not (user_id == current_user.id):
        return bad_request(message="Invalid Request. This is Not Ur Chat.")
        #pass
    chat = Chat.query.filter(or_(Chat.to == user_id, Chat.fro == user_id)).order_by(Chat.updated.desc()).all()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Chat.to_dict(chat, page, per_page, 'chat_api.get_chat')
    return jsonify(data) """

@chat_api.route('/chat/<int:id>', methods=['GET'])
#@token_auth.login_required
def get_chat(id):

    if current_user.is_authenticated and not (id == current_user.id):
        return bad_request(message="Invalid Request. This is Not Ur Chat.")
    chat = Chat.query.filter(or_(Chat.to == id, Chat.fro == id)).order_by(Chat.updated.desc())
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Chat.to_collection_dict(chat, page, per_page, 'chat_api.get_chat', id=id)
    return jsonify(data)
  
@chat_api.route('/chat', methods=['PUT'])
def update_chat():
    data = request.get_json() or {}
    chat_id = data.get('id')  # Assuming you send the chat ID in the JSON data
    if chat_id is None:
        return bad_request('Chat-id is missing in the request data')
    chat = Chat.query.get(chat_id)
    if chat is None:
        return bad_request('Chat not found')
    
    if not (chat.fro == current_user.id):
        return bad_request(message="Invalid Request. This is Not Ur Chat.")
    
    chat.from_dict(data, new_chat=False)
    db.session.commit()
    return jsonify(chat.to_dict())

@chat_api.route('/chat/<int:id>', methods=['GET'])
#@token_auth.login_required
def remove_chat(id):  # Use 'id' as the parameter name
    chat = Chat.query.get(id)  # Replace 'chat_id' with 'id'
    if chat:
        if not (chat.fro == current_user.id or chat.to == current_user.id):
            return bad_request(message="Invalid Request. This is Not Ur Chat.")
        if chat.fro == current_user.id:
            chat.fro_del = True
        else:
            chat.to_del = True
        db.session.commit()  # Commit the session once
        return response('Success! Chat Removed For You')
    return bad_request('Oops! Invalid Chat Request')

