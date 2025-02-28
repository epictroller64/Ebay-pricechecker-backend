from flask import Flask, request, jsonify
from flask_cors import CORS
from checker import Checker

app = Flask(__name__)
CORS(app)

checker = Checker()

@app.route('/api/listings', methods=['GET'])
async def get_listings():
    listings = await checker.get_all_listings()
    # Convert listings to a list of dictionaries
    listings_json = [listing.to_dict() for listing in listings]
    return jsonify(listings_json)

@app.route('/api/listings', methods=['POST']) 
async def add_listing():
    data = request.get_json()
    print(data)
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing url parameter'}), 400
        
    insert_result = await checker.add_listing(data['url'])
    if insert_result:
        return jsonify({'success': True, 'id': insert_result})
    else:
        return jsonify({'error': 'Failed to add listing'}), 500

if __name__ == '__main__':
    app.run(port=3000)
