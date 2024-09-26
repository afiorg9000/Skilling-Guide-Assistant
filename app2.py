from flask import Flask
from routes.permissions import permissions_bp
from routes.assistant import assistant_bp
from services.permissions import PermissionsService
from flask import render_template, Blueprint, request, current_app
from services.assistant import *
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'fa86766c4d9d4f36f20af2577da21a7f'

@app.route('/test')
def hello_world():
    return 'Hello, World from 6000!'

@app.route('/')
def home():
    title = "Ma Page d'Accueil"
    items = ['Pommes', 'Oranges', 'Bananes', 'Mangues']
    return render_template('home.html', title=title, items=items)

@app.route('/user/<int:username>/permissions')
def user_permissions(user_id):
    username = 'User' + str(user_id)
    json_response = {'username': username, 'permissions': 'read'}
    return render_template('json.html', json_response=json_response)


@app.route('/permissions/<username>', methods=['GET'])
def get_permissions(username):
    """
    Endpoint to return the permissions of a user by their username.
    """
    # Get user ID by username
    user_id_response = current_app.permissions_service.get_user_id_by_username(username)
    if user_id_response[1] != 200:
        return render_template('json.html', json_response=user_id_response[0]), user_id_response[1]
    
    user_id = user_id_response[0]['user_id']
    
    # Get permissions by user ID
    permissions_response = current_app.permissions_service.get_permissions_by_user_id(user_id)
    return render_template('json.html', json_response=permissions_response[0]), permissions_response[1]

@app.route('/permissions/<username>/update', methods=['POST'])
def update_permissions(username):
    """
    Endpoint to update a user's permission by their username.
    """
    # Ensure request is JSON and has required data
    if not request.json or 'permission' not in request.json or 'value' not in request.json:
        return render_template('json.html', json_response={'error': 'Bad request, JSON body with "permission" and "value" required'}), 400
    
    permission = request.json['permission']
    value = request.json['value']
    
    # Get user ID by username
    user_id_response = current_app.permissions_service.get_user_id_by_username(username)
    if user_id_response[1] != 200:
        return render_template('json.html', json_response=user_id_response[0]), user_id_response[1]
    
    user_id = user_id_response[0]['user_id']
    
    # Update permission for the user
    update_response = current_app.permissions_service.update_user_permission(user_id, permission, value)
    return render_template('json.html', json_response=update_response[0]), update_response[1]

@app.route('/assistant', methods=['GET', 'POST'])
def assistant():
    if request.method == 'POST':
        # Extract message from the POST request
        data = request.get_json()
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'No message provided'}), 400
      
        assistant_service = AssistantService()

        # Here you would typically process the message and generate a response
        # For demonstration, let's just echo the message back
        assistant_response = assistant_service.run_assistant(message)
        
        # Return response as JSON for the fetch call in home.html
        return jsonify({'assistant_response': assistant_response})
    else:
        # For GET requests, show the form without any initial response
        return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port='5000')
