import schedule
from database import setup_database
from env import DBFILE
from ldapSync import schedule_sync_ldap_to_database
from Webserver import run_webServer_thread

setup_database(DBFILE)
run_webServer_thread()
schedule_sync_ldap_to_database(DBFILE)

while True:
    schedule.run_pending()
