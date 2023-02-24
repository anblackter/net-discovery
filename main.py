import sys
from tools.file_format import RancidFileFormat, PortalFileFormat, PortalFileDepuration
from tools.consolidate_pes import hello
from tools.db_service import init_db, populate_table, update_table, run_query, alter_query

def read_args():
    arguments = sys.argv
    arguments.pop(0)

    if arguments == []:
        # file_format = FileFormat()
        # file_format.get_info()
        #hello()
        #populate_table('ci_security_ip')
        #populate_table('cispec')
        file_portal_format = PortalFileFormat()
        file_portal_format.get_info()
        file_portal_depurate = PortalFileDepuration()
        file_portal_depurate.depurate()
    elif "-f" in arguments:
        file_format = RancidFileFormat()
        file_format.get_info()
        file_portal_format = PortalFileFormat()
        file_portal_format.get_info()
        file_portal_depurate = PortalFileDepuration()
        file_portal_depurate.depurate()

    elif "-d" in arguments:
        init_db()
    elif "-p" in arguments:
        populate_table('rancid')
        update_table('rancid')
        populate_table('soc_transition')
        populate_table('soc')
        update_table('soc')
        populate_table('ci_security')
        populate_table('ci_security_ip_transition')
        populate_table('ci_security_ip')
        update_table('ci_security_ip')
        populate_table('cispec')
    elif "-q" in arguments:
        query = "SELECT * FROM SSCD_CISPEC WHERE ALNVALUE REGEXP '(?:[0-9]{1,3}\\.){3}[0-9]{1,3}'"
        run_query(query)
    elif "-t" in arguments:
        query = "ALTER TABLE SSCD_CI_SECURITY_IP ADD COLUMN NMAP_PORTS VARCHAR(500)"
        alter_query(query)
        query = "ALTER TABLE SSCD_CI_SECURITY_IP ADD COLUMN LOGIN_MGT VARCHAR(60)"
        alter_query(query)
        query = "ALTER TABLE SSCD_CI_SECURITY_IP ADD COLUMN OS_VERSION VARCHAR(500)"
        alter_query(query)
    else:
        return print("")

def run():

    try:
        read_args()
    except KeyboardInterrupt:
        print('\nKeyboard Interrupt')

if __name__ == '__main__':
    run()