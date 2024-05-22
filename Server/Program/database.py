from datetime import datetime
import sqlite3
from env import *

# Function to check if a table exists in the database
def table_exists(cursor, table_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

# Function to create the Users table
def create_users_table(cursor):
    cursor.execute('''CREATE TABLE Users (
                        upn TEXT PRIMARY KEY,
                        rFIDUID TEXT,
                        MemberOf TEXT,
                        FOREIGN KEY (MemberOf) REFERENCES Groups(cn)
                    )''')

# Function to create the Groups table
def create_groups_table(cursor):
    cursor.execute('''CREATE TABLE Groups (
                        cn TEXT PRIMARY KEY
                    )''')

# Function to create the Doors table
def create_doors_table(cursor):
    cursor.execute('''CREATE TABLE Doors (
                        id INTEGER PRIMARY KEY,
                        GroupCn TEXT,
                        FOREIGN KEY (GroupCn) REFERENCES Groups(cn)
                    )''')
# Function to create the logs table
def create_logs_table(cursor):
    """
    Create a log table with columns id, timestamp, user, and granted.
    
    :param db_file: The database file path.
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT ,
            user TEXT ,
            rFIDUID TEXT,
            door_id INTEGER ,
            granted BOOLEAN ,
            FOREIGN KEY (door_id) REFERENCES Doors (id)
            FOREIGN KEY (user) REFERENCES Users (upn)
            FOREIGN KEY (rFIDUID) REFERENCES Users (rFIDUID)            
        )
    ''')
# Function to setup the database
def setup_database(db_file):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Check and create Users table
    if not table_exists(cursor, "Users"):
        create_users_table(cursor)
        print(f"[{datetime.now()}] Users table created successfully.")
    else:
        print(f"[{datetime.now()}] Users table already exists.")

    # Check and create Groups table
    if not table_exists(cursor, "Groups"):
        create_groups_table(cursor)
        print(f"[{datetime.now()}] Groups table created successfully.")
    else:
        print(f"[{datetime.now()}] Groups table already exists.")

    # Check and create Doors table
    if not table_exists(cursor, "Doors"):
        create_doors_table(cursor)
        print(f"[{datetime.now()}] Doors table created successfully.")
    else:
        print(f"[{datetime.now()}] Doors table already exists.")
        # Check and create Doors table
    if not table_exists(cursor, "Log"):
        create_logs_table(cursor)
        print(f"[{datetime.now()}] Log table created successfully.")
    else:
        print(f"[{datetime.now()}] Log table already exists.")
    # Commit changes and close connection
    conn.commit()
    conn.close()

def log_access_attempt(db_file, user, rFIDUID, granted, doorID):
    """
    Log an access attempt to the log table.
    
    :param db_file: The database file path.
    :param user: The user attempting access.
    :param rFIDUID: The user's tag uid
    :param granted: Whether access was granted (True/False).
    :param doorID: The door id
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    

    print(f'[{datetime.now()}] User {user} get granted : {granted} on door : {doorID}')
    cursor.execute('''
        INSERT INTO log (timestamp, user, rFIDUID, granted, door_id) VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now(), user, rFIDUID, granted, doorID))
    
    conn.commit()
    conn.close()
def print_users_table(cursor):
    cursor.execute("SELECT * FROM Users")
    rows = cursor.fetchall()
    print("Users:")
    for row in rows:
        print(row)

# Function to print the content of the Groups table
def print_groups_table(cursor):
    cursor.execute("SELECT * FROM Groups")
    rows = cursor.fetchall()
    print("Groups:")
    for row in rows:
        print(row)

# Function to print the content of the Doors table
def print_doors_table(cursor):
    cursor.execute("SELECT * FROM Doors")
    rows = cursor.fetchall()
    print("Doors:")
    for row in rows:
        print(row)
# Function to print the content of the Log table
def print_log_table(cursor):
    cursor.execute("SELECT * FROM log")
    rows = cursor.fetchall()
    print("Logs:")
    for row in rows:
        print(row)

# Function to print the content of the entire database
def print_database_content(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    print_users_table(cursor)
    print_groups_table(cursor)
    print_doors_table(cursor)
    print_log_table(cursor)
    
    conn.close()
    
def get_logs():

    """
    Fetch all logs from the log table in the database.
    :return: List of log records.
    """
    conn = sqlite3.connect(DBFILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT timestamp, user, rFIDUID, granted, door_id
    FROM log 
    ORDER BY id DESC 
    ''')

    logs = cursor.fetchall()
    
    conn.close()
    return logs


def get_latest_logs(db_file,limit=10):
    """
    Fetch the latest logs from the database.
    
    :param limit: The number of latest logs to fetch.
    :return: List of log entries.
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, user, rFIDUID, granted, door_id
        FROM log 
        ORDER BY id DESC 
        LIMIT ?
    ''', (limit,))
    
    logs = cursor.fetchall()
    conn.close()
    return logs
# Function to fetch list of existing groups from the database
def get_existing_groups(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT cn FROM Groups")
        groups = cursor.fetchall()
        conn.close()
        return [group[0] for group in groups]
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
        return []
    
def get_users():
    """
    Fetch all users from the Users table in the database.
    :return: List of user records.
    """
    conn = sqlite3.connect(DBFILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT upn, rFIDUID, MemberOf FROM Users')
    users = cursor.fetchall()
    
    conn.close()
    return users
# Function to add a door to the database
def add_door_to_database(db_file, group_cn, Door_id):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Doors (id, GroupCn) VALUES (?,?)", (Door_id,group_cn,))
        conn.commit()
        conn.close()
        #print_database_content(DBFILE)
        return True
    except sqlite3.Error as e:
        #print_database_content(DBFILE)
        print(f"SQLite Error: {e}")
        return (False, e)
    
# Function to verify if the user is allowed to open the door
def check_access(rfid_uid_str, door_id):
    try:
        conn = sqlite3.connect(DBFILE)  # Update with your database file path
        cursor = conn.cursor()

        # Convert the received RFID UID string to bytes
        rfid_uid_bytes = rfid_uid_str.encode('utf-8')

        # Get the user's UPN and group memberships based on the RFID UID
        cursor.execute("SELECT upn, MemberOf FROM Users WHERE rFIDUID = ?", (rfid_uid_bytes,))
        user_data = cursor.fetchone()
        if user_data is None:
            return False, None  # User not found

        upn_bytes, user_groups = user_data

        # Decode the UPN bytes to string
        upn = upn_bytes.decode('utf-8')

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