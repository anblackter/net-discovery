# net-discovery
Network discovery for Managed devices in the Network whitout tracking and backup. The project uses primary ARP and Netmiko.

CISPEC.csv --> Table filtered in SCCD database whit query :

SELECT CISPECID, ALNVALUE, ASSETATTRID, CINUM, CHANGEDATE
FROM MAXIMO.CISPEC
WHERE ALNVALUE IS NOT NULL

pes_consolidated --> list of PEs from RancidPE01, information consolidated with a python script and transfered by SCP

portal_db.csv --> File exported from  http://portal-csc.cscsmart.com:5001/soc and change the format from excel to csv

rancid_db.csv --> constructed from resultado_total.txt  with tools/file_format.py. resultado_total.txt copy from RancidCP01 via SCP

SCCD_SECURITY_QUERY.csv --> exported from web interface of SSCD  https://servicedesk.cwc.com/maximo/ui/?event=loadapp&value=ccci&uisessionid=5720&csrftoken=m0mdt6luegn62c6ehl8u3nvegm classifcation = "guard, threat, security, firewall, forti, advance"


COMMIT NOTES:
--> (81246b5) "First Project Layout working. SSCD connection, Local Management Database, Net Tools (ping, nmap)"
    1. Connection with SSCD Oracle Database - run queries and store data to .csv files (Docker py_dbs image)
    2. Several Tools Defined and working:
        2.1 Rancid_File_Format for read info from Rancid and parse as .csv file
        2.2 db_service for create and manage a local sqlite database in which all the Tables are stored (Portal_SOC, RANCID, SSCD_FW, SSCD_FW_IP)
        2.3 Ping tool for create a thread and run multiple ping to the Firewalls with valid IPs
        2.4 Nmap tool for search open ports

--> (4b2a9fa) "Alpha Backend version of the project working. SSCD connection, Local Management Database, Net Tools (ping, nmap, ssh and REST Api)"
    1. Connection with SSCD Oracle Database - run queries and store data to .csv files (Docker py_dbs image)
    2. Several Tools Defined and working:
        2.1 Rancid_File_Format for read info from Rancid and parse as .csv file
        2.2 db_service for create and manage a local sqlite database in which all the Tables are stored (Portal_SOC, RANCID, SSCD_FW, SSCD_FW_IP)
        2.3 Ping tool for create a thread and run multiple ping to the Firewalls with valid IPs
        2.4 Nmap tool for search open ports
        2.5 SSH tool for try to login into the devices and get the result of 'get system status' command
        2.6 REST Api connectivity for try to login into the devices and get the result of '/api/v2/cmdb/system/global'

--> "Netcool DB include and all the project working"