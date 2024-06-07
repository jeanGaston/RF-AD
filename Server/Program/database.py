from datetime import datetime
import sqlite3
from env import DBFILE


# Function to check if a table exists in the database
def table_exists(cursor, table_name):
    """
    Check if a table exists in the database.

    This function checks whether a table with the specified name exists in the database.

    ## Parameters:
    - cursor (sqlite3.Cursor): The cursor object to execute SQL queries.
    - table_name (str): The name of the table to check.

    ## Returns:
    - bool: True if the table exists, False otherwise.
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    return cursor.fetchone() is not None


# Function to create the Users table
def create_users_table(cursor):
    """
    Create the Users table in the database.

    This function creates the Users table with columns for user principal name (upn), RFID UID, and member of groups.

    ## Parameters:
    - cursor (sqlite3.Cursor): The cursor object to execute SQL queries.
    """
    cursor.execute("""CREATE TABLE Users (
                        upn TEXT PRIMARY KEY,
                        rFIDUID TEXT,
                        MemberOf TEXT,
                        FOREIGN KEY (MemberOf) REFERENCES Groups(cn)
                    )""")


# Function to create the Groups table
def create_groups_table(cursor):
    """
    Create the Groups table in the database.

    This function creates the Groups table with a single column for common name (cn) of the group.

    ## Parameters:
    - cursor (sqlite3.Cursor): The cursor object to execute SQL queries.
    """
    cursor.execute("""CREATE TABLE Groups (
                        cn TEXT PRIMARY KEY
                    )""")


# Function to create the Doors table
def create_doors_table(cursor):
    """
    Create the Doors table in the database.

    This function creates the Doors table with columns for door ID and associated group common name.

    ## Parameters:
    - cursor (sqlite3.Cursor): The cursor object to execute SQL queries.
    """
    cursor.execute("""CREATE TABLE Doors (
                        id INTEGER PRIMARY KEY,
                        GroupCn TEXT,
                        FOREIGN KEY (GroupCn) REFERENCES Groups(cn)
                    )""")


# Function to create the logs table
def create_logs_table(cursor):
    """
    Create the logs table in the database.

    This function creates the logs table with columns for ID (auto-incremented), timestamp, user, RFID UID, door ID,
    and access granted status. Foreign key constraints are set on the door ID, user, and RFID UID columns.

    ## Parameters:
    - cursor (sqlite3.Cursor): The cursor object to execute SQL queries.
    """
    cursor.execute("""
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
    """)


# Function to setup the database
def setup_database(db_file):
    """
    Set up the SQLite database by creating necessary tables if they don't already exist.

    This function checks if the Users, Groups, Doors, and Log tables exist in the database. If any of them don't exist,
    it creates them using their respective creation functions. After creating or verifying the tables, it commits
    the changes and closes the database connection.

    ## Parameters:
    - db_file (str): The file path to the SQLite database.

    ## Returns:
    - None
    """
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
    Log an access attempt to the database.

    This function inserts a new entry into the log table of the SQLite database, recording details about the access attempt,
    such as the timestamp, user, RFID UID, whether access was granted, and the door ID.

    ## Parameters:
    - db_file (str): The file path to the SQLite database.
    - user (str): The user's UPN (User Principal Name).
    - rFIDUID (str): The RFID UID associated with the access attempt.
    - granted (bool): A boolean indicating whether access was granted (True) or denied (False).
    - doorID (int): The ID of the door where the access attempt occurred.

    # Returns:
    - None
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    print(f"[{datetime.now()}] User {user} get granted : {granted} on door : {doorID}")
    cursor.execute(
        """
        INSERT INTO log (timestamp, user, rFIDUID, granted, door_id) VALUES (?, ?, ?, ?, ?)
    """,
        (datetime.now(), user, rFIDUID, granted, doorID),
    )

    conn.commit()
    conn.close()


def print_users_table(cursor):
    """
    Print the content of the Users table.

    ## Parameters:
    - cursor (sqlite3.Cursor): Cursor object for executing SQLite queries.
    """
    cursor.execute("SELECT * FROM Users")
    rows = cursor.fetchall()
    print("Users:")
    for row in rows:
        print(row)


# Function to print the content of the Groups table
def print_groups_table(cursor):
    """
    Print the content of the Groups table.

    ## Parameters:
    - cursor (sqlite3.Cursor): Cursor object for executing SQLite queries.
    """   
    cursor.execute("SELECT * FROM Groups")
    rows = cursor.fetchall()
    print("Groups:")
    for row in rows:
        print(row)


# Function to print the content of the Doors table
def print_doors_table(cursor):
    """
    Print the content of the Doors table.

    ## Parameters:
    - cursor (sqlite3.Cursor): Cursor object for executing SQLite queries.
    """
    cursor.execute("SELECT * FROM Doors")
    rows = cursor.fetchall()
    print("Doors:")
    for row in rows:
        print(row)


# Function to print the content of the Log table
def print_log_table(cursor):
    """
    Print the content of the Log table.

    ## Parameters:
    - cursor (sqlite3.Cursor): Cursor object for executing SQLite queries.
    """
    cursor.execute("SELECT * FROM log")
    rows = cursor.fetchall()
    print("Logs:")
    for row in rows:
        print(row)


# Function to print the content of the entire database
def print_database_content(db_file):
    """
    Print the content of the entire database.

    ## Parameters:
    - db_file (str): The file path to the SQLite database.
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    print_users_table(cursor)
    print_groups_table(cursor)
    print_doors_table(cursor)
    # print_log_table(cursor)

    conn.close()


def get_logs():
    """
    Fetch all logs from the log table in the database.
    
    ## Returns:
    - list: List of log records.
    """
    conn = sqlite3.connect(DBFILE)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT timestamp, user, rFIDUID, granted, door_id
    FROM log 
    ORDER BY id DESC 
    """)

    logs = cursor.fetchall()

    conn.close()
    return logs


def get_latest_logs(db_file, limit=10):
    """
    Fetch the latest logs from the database.

    ## Parameters:
    - db_file (str): The file path to the SQLite database.
    - limit (int): The number of latest logs to fetch. Default is 10.

    ## Returns:
    - list: List of log entries.
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT timestamp, user, rFIDUID, granted, door_id
        FROM log 
        ORDER BY id DESC 
        LIMIT ?
    """,
        (limit,),
    )

    logs = cursor.fetchall()
    conn.close()
    return logs


# Function to fetch list of existing groups from the database
def get_existing_groups(db_file):
    """
    Fetches a list of existing groups from the database.

    ## Parameters: 
        - db_file (str): The file path to the SQLite database.

    ## Returns:
        - list: List of existing group names.
    """
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


def delete_group_from_database(group_cn):
    """
    Delete a group from the database.

    This function deletes a group with the specified common name (cn) from both the Groups and Doors tables
    in the database.

    ## Parameters:
    - group_cn (str): The common name of the group to delete.
    """
    conn = sqlite3.connect(DBFILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Groups WHERE cn = ?", (group_cn,))
    cursor.execute("DELETE FROM Doors WHERE GroupCn = ?", (group_cn,))
    conn.commit()
    conn.close()


def get_doors():
    """
    Retrieve all doors from the database.

    This function fetches all rows from the Doors table in the database and returns them as a list of tuples.

    ## Returns:
    - list: A list of tuples representing door records.
    """
    conn = sqlite3.connect(DBFILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Doors")
    doors = cursor.fetchall()
    conn.close()
    return doors


def get_users():
    """
    Fetch all users from the Users table in the database.
    
    ## Returns:
        - list: List of user records.
    """
    conn = sqlite3.connect(DBFILE)
    cursor = conn.cursor()

    cursor.execute("SELECT upn, rFIDUID, MemberOf FROM Users")
    users = cursor.fetchall()

    conn.close()
    return users


# Function to add a door to the database
def add_door_to_database(db_file, group_cn, Door_id):
    """
    Add a door to the database.

    This function inserts a new door record into the Doors table with the specified group common name (cn)
    and door ID.

    ## Parameters:
        - db_file (str): The file path to the SQLite database.
        - group_cn (str): The common name of the group associated with the door.
        - Door_id (int): The ID of the door.

    ## Returns:
        - bool: True if the door was added successfully, False otherwise.
    ## Raises:
        - sqlite3.Error: If there's an error executing the SQL query.
    """
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Doors (id, GroupCn) VALUES (?,?)",
            (
                Door_id,
                group_cn,
            ),
        )
        conn.commit()
        conn.close()
        # print_database_content(DBFILE)
        return True
    except sqlite3.Error as e:
        # print_database_content(DBFILE)
        print(f"SQLite Error: {e}")
        return (False, e)


# Function to verify if the user is allowed to open the door
def check_access(rfid_uid_str, door_id):
    """
    Check if the user is allowed to open the door.

    This function verifies if the user associated with the given RFID UID is allowed to open the door
    specified by the door ID.

    ## Parameters:
        - rfid_uid_str (str): The RFID UID of the user.
        - door_id (int): The ID of the door.

    ## Returns:
        - tuple: A tuple containing a boolean value indicating access permission and the user's UPN
               if access is granted, otherwise (False, None).
    ## Raises:
        - sqlite3.Error: If there's an error executing the SQL query.
    """
    try:
        conn = sqlite3.connect(DBFILE)  # Update with your database file path
        cursor = conn.cursor()

        # Convert the received RFID UID string to bytes
        rfid_uid_bytes = rfid_uid_str.encode("utf-8")

        # Get the user's UPN and group memberships based on the RFID UID
        cursor.execute(
            "SELECT upn, MemberOf FROM Users WHERE rFIDUID = ?", (rfid_uid_bytes,)
        )
        user_data = cursor.fetchone()
        if user_data is None:
            return False, None  # User not found

        upn_bytes, user_groups = user_data

        # Decode the UPN bytes to string
        upn = upn_bytes.decode("utf-8")

        # Get the group associated with the door
        cursor.execute("SELECT GroupCn FROM Doors WHERE id = ?", (door_id,))
        door_group = cursor.fetchone()
        if door_group is None:
            return False, None  # Door not found

        door_group = door_group[0]

        # Check if the user's group is allowed to open the door
        if door_group in user_groups.split(","):
            return True, upn  # Access granted
        else:
            return False, None  # Access denied

    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
        return False, None
