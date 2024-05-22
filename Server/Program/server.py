from ldapSync import *
from database import *
from Webserver import run_webServer_thread
from env import *
import schedule



setup_database(DBFILE)
print_database_content(DBFILE)
run_webServer_thread()
schedule_sync_ldap_to_database(DBFILE)

while True :
    schedule.run_pending()