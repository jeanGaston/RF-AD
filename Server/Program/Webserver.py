import io
from threading import Thread

from database import (
    add_door_to_database,
    check_access,
    delete_group_from_database,
    get_doors,
    get_existing_groups,
    get_latest_logs,
    get_logs,
    get_users,
    log_access_attempt,
)
from env import DBFILE, WebServerPORT
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
)
from ldapSync import sync_ldap_to_database

app = Flask(__name__)


# Route to the home
@app.route("/")
def index():
    existing_groups = get_existing_groups(DBFILE)  # Update with your database file path
    logs = get_latest_logs(DBFILE, 5)
    # print(logs[0])
    return render_template("./index.html", existing_groups=existing_groups, logs=logs)


# Route to display the fuser db
@app.route("/UserDB")
def usersdb():
    users = get_users()
    return render_template("userdb.html", users=users)


# Route to display the fuser db
@app.route("/LogsDB")
def logsdb():
    logs = get_logs()
    return render_template("logsdb.html", logs=logs)


@app.route("/export_logs")
def export_logs():
    logs = get_logs()

    # Create a file-like string to write logs
    log_output = io.StringIO()
    log_line = "TimeStamp,User,Tag UID,Door ID,Granted,\n"
    log_output.write(log_line)
    for log in logs:
        log_line = f"{log[0]},{log[1]},{log[2]},{log[4]},{'Yes' if log[3] else 'No'},\n"
        log_output.write(log_line)

    # Set the position to the beginning of the stream
    log_output.seek(0)

    # Create a response with the file data
    return Response(
        log_output,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=logs.csv"},
    )


@app.route("/GroupsDB")
def groupsdb():
    doors = get_doors()
    groups = get_existing_groups(DBFILE)
    return render_template("groupsdb.html", doors=doors, groups=groups)


@app.route("/delete_group/<group_cn>", methods=["POST"])
def delete_group(group_cn):
    delete_group_from_database(group_cn)
    return render_template("./index.html")


# Route to handle form submission and add the door to the database
@app.route("/add_door", methods=["POST"])
def add_door():
    Door_id = request.form["Door_id"]
    group_cn = request.form["group_cn"]

    # Update with your database file path
    if add_door_to_database(DBFILE, group_cn, Door_id):
        return redirect("/")
    return "Failed to add door to the database."


# Route to handle sync button click
@app.route("/sync")
def sync():
    sync_ldap_to_database(DBFILE)
    return render_template("./LDAP.html")


# Route to handle door access requests
@app.route("/access", methods=["POST"])
def door_access():
    data = request.get_json()
    rfid_uid = data.get("rfid_uid")
    door_id = data.get("door_id")

    if rfid_uid is None or door_id is None:
        return jsonify({"error": "RFID UID and door ID are required"}), 400

    access_granted, upn = check_access(rfid_uid, door_id)
    if access_granted:
        log_access_attempt(DBFILE, upn, rfid_uid, True, door_id)
        return jsonify({"access_granted": True, "upn": upn}), 200

    log_access_attempt(DBFILE, upn, rfid_uid, False, door_id)
    return jsonify({"access_granted": False}), 403


def run_flask_app():
    """Run the Flask web application.

    This function starts the Flask web application with debugging enabled,
    no reloader, on the specified port and host. It serves as the main entry
    point for running the web server.
    """
    app.run(debug=True, use_reloader=False, port=WebServerPORT, host="0.0.0.0")


def run_webServer_thread():
    """Start the Flask web server in a separate thread.

    This function initializes and starts a new thread to run the Flask web
    application. It allows the web server to run concurrently with other
    tasks in the main program, ensuring the web interface remains responsive.
    """
    print(f"STARTING WEB SERVER ON PORT {WebServerPORT}")
    flask_thread = Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    # flask_thread.join()


if __name__ == "__main__":
    app.run(debug=True)
