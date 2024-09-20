from flask import Flask, jsonify, render_template, request
import requests
from main import *

app = Flask(__name__)

# Function to get sports lists from the Odds API
def get_sport_lists(api_key=''):
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={api_key}'
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Failed to retrieve data. Status code: {response.status_code}')
        return None

# API endpoint to get the sports list
@app.route('/api/sports')
def sports_list():
    api_key = '519258381ccabcc46b67839ad7e1a04d' 
    sports = get_sport_lists(api_key)
    
    if sports:
        return jsonify(sports)
    else:
        return jsonify({'error': 'Failed to fetch sports data'}), 500

# New chatbot API endpoint
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    if request.method == 'POST':
        # Get the message and sportKey from the request
        data = request.get_json()
        user_message = data.get('message', '')
        sport_key = request.args.get('sportKey', '')

        # Example response (you would replace this with your AI/chatbot logic)
        # response_message = f"You asked about {sport_key}. Your message: {user_message}"
        pred = make_sport_pred(sport_key, user_message)
        print(pred)

        return jsonify({'response': pred})

# Default route to render the frontend page
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5500)
