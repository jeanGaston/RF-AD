#!/bin/sh
ls /app/Program
# Create env.py with environment variables
cat <<EOT > /app/env.py
LDAPUSER = "${LDAPUSER}"
LDAPPASS = "${LDAPPASS}"
LDAP_SERVER = "${LDAP_SERVER}"
DOOR_ACCESS_GROUPS_DN = "${DOOR_ACCESS_GROUPS_DN}"
USERS_DN = "${USERS_DN}"
DBFILE = "${DBFILE}"
WebServerPORT = ${WebServerPORT}
EOT


# Run the main server script
exec python3 /Program/server.py
