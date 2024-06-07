import sqlite3
import threading
from datetime import datetime

import ldap
import schedule
from env import DOOR_ACCESS_GROUPS_DN, LDAP_SERVER, LDAPPASS, LDAPUSER, USERS_DN


# Function to initialize LDAP connection
def initialize_ldap_connection():
    """Initialize the LDAP connection.

    This function attempts to establish a connection to the LDAP server using the provided server address,
    user credentials, and settings. If the connection is successful, it returns the connection object.
    In case of an error, it prints the error and returns None.

    ## Returns:
    - ldap.LDAPObject or None: The LDAP connection object if successful, otherwise None.
    """
    try:
        connect = ldap.initialize(LDAP_SERVER)
        connect.set_option(ldap.OPT_REFERRALS, 0)
        connect.simple_bind_s(LDAPUSER, LDAPPASS)
        print(f"[{datetime.now()}] LDAP connection successful.")
        return connect
    except ldap.LDAPError as e:
        print(f"[{datetime.now()}] LDAP Error: {e}")
        return None


# Function to retrieve users from LDAP
def retrieve_users_from_ldap(ldap_connection):
    """Retrieve users from LDAP.

    This function searches the LDAP directory for users within the specified base DN and returns the search result.
    It searches for objects with the 'user' object class within the subtree of the specified base DN.

    ## Parameters:
    - ldap_connection (ldap.LDAPObject): The LDAP connection object.

    ## Returns:
    - list of tuple: A list of tuples containing the search result, where each tuple represents a user entry.
                   Each tuple consists of the DN (Distinguished Name) of the user entry and its attributes.
                   Returns an empty list if an error occurs during the LDAP search.
    """
    try:
        result = ldap_connection.search_s(
            USERS_DN,
            ldap.SCOPE_SUBTREE,
            "(objectClass=user)",
        )
        return result
    except ldap.LDAPError as e:
        print(f"[{datetime.now()}] LDAP Error: {e}")
        return []


# Function to retrieve groups from LDAP
def retrieve_groups_from_ldap(ldap_connection):
    """Retrieve groups from LDAP.

    This function searches the LDAP directory for groups within the specified base DN and returns the search result.
    It searches for objects with the 'group' object class within the subtree of the specified base DN.

    ## Parameters:
    - ldap_connection (ldap.LDAPObject): The LDAP connection object.

    ## Returns:
    - list of tuple: A list of tuples containing the search result, where each tuple represents a group entry.
                   Each tuple consists of the DN (Distinguished Name) of the group entry and its attributes.
                   Returns an empty list if an error occurs during the LDAP search.
    """
    try:
        result = ldap_connection.search_s(
            DOOR_ACCESS_GROUPS_DN,
            ldap.SCOPE_SUBTREE,
            "(objectClass=group)",
        )
        return result
    except ldap.LDAPError as e:
        print(f"[{datetime.now()}]LDAP Error: {e}")
        return []


# Function to add user to the database or update if already exists
def add_user_to_database(conn, cursor, upn, rfid_uid, member_of):
    """Add a user to the database or update the user's information if they already exist.

    This function checks if a user with the given UPN (User Principal Name) already exists in the database.
    If the user exists and their RFID UID or group membership has changed, the function updates the user's
    record. If the user does not exist, the function inserts a new record for the user.

    ## Parameters:
    - conn (sqlite3.Connection): The SQLite database connection.
    - cursor (sqlite3.Cursor): The cursor object for executing SQL queries.
    - upn (str): The User Principal Name of the user.
    - rfid_uid (str): The RFID UID associated with the user.
    - member_of (str): The group membership (CN) of the user.

    ## Returns:
    - None

    ## Raises:
    - sqlite3.Error: If an error occurs while accessing the SQLite database.
    """
    try:
        cursor.execute("SELECT * FROM Users WHERE upn=?", (upn,))
        existing_user = cursor.fetchone()
        if existing_user:
            # User already exists, check if data needs to be updated
            if existing_user[1] != rfid_uid or existing_user[2] != member_of:
                cursor.execute(
                    "UPDATE Users SET rFIDUID=?, MemberOf=? WHERE upn=?",
                    (rfid_uid, member_of, upn),
                )
                conn.commit()
                print(f"[{datetime.now()}] User '{upn}' updated in the database.")
            else:
                print(
                    f"[{datetime.now()}] User '{upn}' already exists in the database with the same data.",
                )
        else:
            # User doesn't exist, insert new user
            cursor.execute(
                "INSERT INTO Users (upn, rFIDUID, MemberOf) VALUES (?, ?, ?)",
                (upn, rfid_uid, member_of),
            )
            conn.commit()
            print(f"[{datetime.now()}] User '{upn}' added to the database.")
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")


# Function to add group to the database or update if already exists
def add_group_to_database(conn, cursor, cn):
    """Add a group to the database if it does not already exist.

    This function checks if a group with the given CN (Common Name) already exists in the database.
    If the group exists, it prints a message indicating that the group already exists. If the group
    does not exist, it inserts a new record for the group.

    Parameters
    ----------
    conn (sqlite3.Connection): The SQLite database connection.
    cursor (sqlite3.Cursor): The cursor object for executing SQL queries.
    cn (str): The Common Name of the group.

    Returns
    -------
    None

    Raises
    ------
    sqlite3.Error: If an error occurs while accessing the SQLite database.

    """
    try:
        cursor.execute("SELECT * FROM Groups WHERE cn=?", (cn,))
        existing_group = cursor.fetchone()
        if existing_group:
            # Group already exists, no need to update
            print(f"[{datetime.now()}] Group '{cn}' already exists in the database.")
        else:
            # Group doesn't exist, insert new group
            cursor.execute("INSERT INTO Groups (cn) VALUES (?)", (cn,))
            conn.commit()
            print(f"[{datetime.now()}] Group '{cn}' added to the database.")
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")


# Function to sync LDAP users and groups to the database
def sync_ldap_to_database(db_file):
    """Syncs LDAP users and groups to the SQLite database.

    Args:
    ----
        db_file (str): The path to the SQLite database file.

    Returns:
    -------
        None

    This function connects to the LDAP server, retrieves user and group information,
    and synchronizes it with the SQLite database. It checks if users are disabled in
    LDAP and removes them from the database if necessary. It also ensures that users
    and groups are added or updated in the database according to the LDAP information.

    Note:
    ----
        The LDAP connection must be properly configured and the LDAP server accessible
        from the machine running this script.

    """
    ldap_conn = initialize_ldap_connection()
    if ldap_conn:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Retrieve users from LDAP and add them to the database
        users = retrieve_users_from_ldap(ldap_conn)
        for dn, user_info in users:
            upn = user_info.get("userPrincipalName", [""])[0]
            rfid_uid = user_info.get("rFIDUID", [""])[0]
            member_of = [
                group.decode("utf-8").split(",")[0].split("=")[1]
                for group in user_info.get("memberOf", [])
            ]

            # Check if the user is disabled in LDAP
            user_account_control = user_info.get("userAccountControl", [0])[0]
            if (
                user_account_control == b"514" or user_account_control == b"66050"
            ):  # Check if the 9th bit is set (ADS_UF_ACCOUNTDISABLE flag)
                # User is disabled, check if user exists in the database and remove if present
                cursor.execute("SELECT * FROM Users WHERE upn=?", (upn,))
                existing_user = cursor.fetchone()
                if existing_user:
                    cursor.execute("DELETE FROM Users WHERE upn=?", (upn,))
                    conn.commit()
                    print(
                        f"[{datetime.now()}] User '{upn}' disabled in LDAP and removed from the database.",
                    )
                else:
                    print(
                        f"[{datetime.now()}] User '{upn}' disabled in LDAP but not present in the database.",
                    )
                continue  # Skip adding the disabled user to the database

            # User is not disabled, add or update user in the database
            add_user_to_database(conn, cursor, upn, rfid_uid, ", ".join(member_of))

        # Retrieve groups from LDAP and add them to the database
        groups = retrieve_groups_from_ldap(ldap_conn)
        for dn, group_info in groups:
            cn = group_info.get("cn", [""])[0].decode("utf-8")
            add_group_to_database(conn, cursor, cn)

        # Close connections
        conn.close()
        ldap_conn.unbind()


def run_sync_ldap_to_database_thread(db_file):
    """Run the LDAP synchronization process in a separate thread.

    This function initiates the synchronization of LDAP data to the database in a background thread.
    It ensures that the LDAP synchronization runs asynchronously, allowing the main program to continue
    running without being blocked.

    Parameters
    ----------
    db_file (str): The path to the SQLite database file.

    Returns
    -------
    None

    """
    print(f"[{datetime.now()}] Running LDAP sync")
    threading.Thread(target=sync_ldap_to_database, args=(db_file,), daemon=True).start()


def schedule_sync_ldap_to_database(db_file):
    """Schedule the LDAP synchronization process to run immediately and then every 5 minutes.

    This function runs the LDAP synchronization process in a background thread immediately upon invocation
    and sets up a recurring schedule to run the synchronization every 5 minutes.

    Parameters
    ----------
    db_file (str): The path to the SQLite database file.

    Returns
    -------
    None

    """
    run_sync_ldap_to_database_thread(db_file)  # Run immediately
    schedule.every(5).minutes.do(run_sync_ldap_to_database_thread, db_file)
