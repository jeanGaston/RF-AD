from datetime import datetime
import ldap
import sqlite3
import threading
import schedule
from env import DOOR_ACCESS_GROUPS_DN, LDAPPASS, LDAPUSER, LDAP_SERVER, USERS_DN


# Function to initialize LDAP connection
def initialize_ldap_connection():
    """
    ## Settings :
        None
        ## Behavior
        Init the connection to the LDAP server.
        Return LDAPobjet instance when connected
        if it fail, return None and print error code
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
    """
    ## Settings :
    - ldap_connection : LDAPobjet instance
    ## Behavior
    retrieve the users in the specified OU
    Return result when it success
    if it fail, return empty list and print error code
    """
    try:
        result = ldap_connection.search_s(
            USERS_DN, ldap.SCOPE_SUBTREE, "(objectClass=user)"
        )
        return result
    except ldap.LDAPError as e:
        print(f"[{datetime.now()}] LDAP Error: {e}")
        return []


# Function to retrieve groups from LDAP
def retrieve_groups_from_ldap(ldap_connection):
    """
    ## Settings :
        - ldap_connection : LDAPobjet instance
        ## Behavior
        retrieve the groups in the specified OU
        Return result when it success
        if it fail, return empty list and print error code
    """
    try:
        result = ldap_connection.search_s(
            DOOR_ACCESS_GROUPS_DN, ldap.SCOPE_SUBTREE, "(objectClass=group)"
        )
        return result
    except ldap.LDAPError as e:
        print(f"[{datetime.now()}]LDAP Error: {e}")
        return []


# Function to add user to the database or update if already exists
def add_user_to_database(conn, cursor, upn, rfid_uid, member_of):
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
                    f"[{datetime.now()}] User '{upn}' already exists in the database with the same data."
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
    """
    Syncs LDAP users and groups to the SQLite database.

    Args:
        db_file (str): The path to the SQLite database file.

    Returns:
        None

    This function connects to the LDAP server, retrieves user and group information,
    and synchronizes it with the SQLite database. It checks if users are disabled in
    LDAP and removes them from the database if necessary. It also ensures that users
    and groups are added or updated in the database according to the LDAP information.

    Note:
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
                        f"[{datetime.now()}] User '{upn}' disabled in LDAP and removed from the database."
                    )
                else:
                    print(
                        f"[{datetime.now()}] User '{upn}' disabled in LDAP but not present in the database."
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
    print(f"[{datetime.now()}] Running LDAP sync")
    threading.Thread(target=sync_ldap_to_database, args=(db_file,), daemon=True).start()


def schedule_sync_ldap_to_database(db_file):
    run_sync_ldap_to_database_thread(db_file)  # Run immediately
    schedule.every(5).minutes.do(run_sync_ldap_to_database_thread, db_file)
