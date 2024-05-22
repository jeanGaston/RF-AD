from threading import Thread
from flask import Flask, request, jsonify
from env import *
import sqlite3

app = Flask(__name__)

# Function to verify if the user is allowed to open the door
def check_access(rfid_uid, door_id):
    try:
        conn = sqlite3.connect(DBFILE)  # Update with your database file path
        cursor = conn.cursor()

        # Get the user's UPN and group memberships based on the RFID UID
        cursor.execute("SELECT upn, MemberOf FROM Users WHERE rFIDUID = ?", (rfid_uid,))
        user_data = cursor.fetchone()
        if user_data is None:
            return False, None  # User not found

        upn, user_groups = user_data

        # Get the group associated with the door
        cursor.execute("SELECT GroupCn FROM Doors WHERE id = ?", (door_id,))
        door_group = cursor.fetchone()
        if door_group is None:
            return False, None  # Door not found

        door_group = door_group[0]

        # Check if the user's group is allowed to open the door
        if door_group in user_groups.split(','):
            return True, upn  # Access granted
        else:
            return False, None  # Access denied

    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
        return False, None

# Route to handle door access requests
@app.route('/access', methods=['POST'])
def door_access():
    data = request.get_json()
    rfid_uid = data.get('rfid_uid')
    door_id = data.get('door_id')

    if rfid_uid is None or door_id is None:
        return jsonify({'error': 'RFID UID and door ID are required'}), 400

    access_granted, upn = check_access(rfid_uid, door_id)
    if access_granted:
        return jsonify({'access_granted': True, 'upn': upn}), 200
    else:
        return jsonify({'access_granted': False}), 200

def run_flask_app():
    app.run(debug=True, use_reloader=False, port=WebAPIPORT)
def run_webAPI_thread():
    print(f"STARTING API on port {WebAPIPORT}")
    flask_thread = Thread(target=run_flask_app)
    flask_thread.start()
    flask_thread.join()
    
if __name__ == '__main__':
    app.run(debug=True)
