#!/usr/bin/env python3
import os
import re
from datetime import datetime, timedelta
from db_service import run_query, update_query, get_db

def get_elapsep_time(initial_time):
    step_time = datetime.now()
    diff_time = step_time - initial_time
    elapsed_time = datetime.strptime(str(diff_time), '%H:%M:%S.%f')
    return elapsed_time.strftime('%H:%M:%S.%f')

def run():
    initial_time = datetime.now()
    print(f'INITIAL TIME ------------------ {initial_time}')
    db = get_db()
    UPDATE_SSCD = '''
    INSERT INTO CONSOLIDATED_FW (CONFIG_ITEM, CLASS_DESC, LOCATION_ADDRESS, CUSTOMER_NAME, IP, IN_SSCD)
	SELECT
		CONFIG_ITEM,
        CLASS_DESC,
		LOCATION_ADDRESS,
		CUSTOMER_NAME,
		IP,
		IN_SSCD
	FROM
		SSCD_CI_SECURITY_IP
	GROUP BY IP
    '''
    update_query(UPDATE_SSCD)
    print(' INSERT INTO CONSOLIDATED_FW SSCD !!!')

    sscd_lines = run_query('SELECT * FROM CONSOLIDATED_FW')
    counter = 0
    updates = []
    for line in sscd_lines:
        ip = line['IP']
        query = db.execute(f"SELECT BACKUP_STATUS, BACKUP_DATE FROM RANCID_DEVICES RD WHERE IP_DCN == '{ip}'").fetchone()
        in_rancid = int(db.execute(f"SELECT COUNT(IP_DCN) FROM RANCID_DEVICES rd WHERE IP_DCN = '{ip}'").fetchone()['COUNT(IP_DCN)'])
        in_portal = int(db.execute(f"SELECT COUNT(IP) FROM PORTAL_SOC_FW PSF WHERE IP = '{ip}'").fetchone()['COUNT(IP)'])
        in_netcool = int(db.execute(f"SELECT COUNT(IP_DCN) FROM NETCOOL_FW ND WHERE IP_DCN = '{ip}'").fetchone()['COUNT(IP_DCN)'])
        if query != None:
            backup_status = query['BACKUP_STATUS']
            backup_date = query['BACKUP_DATE']
            updates.append(f'UPDATE CONSOLIDATED_FW SET BACKUP_STATUS = "{backup_status}", BACKUP_DATE = "{backup_date}", \
                            IN_RANCID = {in_rancid}, IN_PORTAL = {in_portal}, IN_NETCOOL = {in_netcool} WHERE IP = "{ip}"')
        else:
            backup_status = 'sin'
            backup_date = 'sin_fecha'
            updates.append(f'UPDATE CONSOLIDATED_FW SET BACKUP_STATUS = "{backup_status}", BACKUP_DATE = "{backup_date}", \
                            IN_RANCID = {in_rancid}, IN_PORTAL = {in_portal}, IN_NETCOOL = {in_netcool} WHERE IP = "{ip}"')
        # print(ip, in_rancid, in_portal, backup_status, backup_date, sep=' -- ')
        # counter += 1
        # if counter > 199:
        #     break
    # print(updates)
    #print(f'ENLAPSED TIME ------------------ {get_elapsep_time(initial_time)} (H:M:S.ms)')

    for update in updates:
        update_query(update)
    print('UPDATE_SSCD !!!')

    updates_rancid = []
    rancid_lines = run_query('SELECT * FROM RANCID_DEVICES')
    for line in rancid_lines:
        ip = line['IP_DCN']
        in_sscd = int(db.execute(f"SELECT COUNT(IP) FROM SSCD_CI_SECURITY_IP rd WHERE IP = '{ip}'").fetchone()['COUNT(IP)'])
        in_portal = int(db.execute(f"SELECT COUNT(IP) FROM PORTAL_SOC_FW PSF WHERE IP = '{ip}'").fetchone()['COUNT(IP)'])
        in_netcool = int(db.execute(f"SELECT COUNT(IP_DCN) FROM NETCOOL_FW ND WHERE IP_DCN = '{ip}'").fetchone()['COUNT(IP_DCN)'])
        updates_rancid.append(f'UPDATE RANCID_DEVICES SET IN_SSCD = {in_sscd}, IN_PORTAL = {in_portal}, IN_NETCOOL = {in_netcool} WHERE IP_DCN = "{ip}"')

    for update in updates_rancid:
        update_query(update)
    print('UPDATE_RANCID !!!')

    updates_portal = []
    portal_lines = run_query('SELECT * FROM PORTAL_SOC_FW')
    for line in portal_lines:
        ip = line['IP']
        in_rancid = int(db.execute(f"SELECT COUNT(IP_DCN) FROM RANCID_DEVICES rd WHERE IP_DCN = '{ip}'").fetchone()['COUNT(IP_DCN)'])
        in_sscd = int(db.execute(f"SELECT COUNT(IP) FROM SSCD_CI_SECURITY_IP rd WHERE IP = '{ip}'").fetchone()['COUNT(IP)'])
        in_netcool = int(db.execute(f"SELECT COUNT(IP_DCN) FROM NETCOOL_FW ND WHERE IP_DCN = '{ip}'").fetchone()['COUNT(IP_DCN)'])
        updates_portal.append(f'UPDATE PORTAL_SOC_FW SET IN_RANCID = {in_rancid}, IN_SSCD = {in_sscd}, IN_NETCOOL = {in_netcool} WHERE IP = "{ip}"')

    for update in updates_portal:
        update_query(update)
    print('UPDATE_PORTAL !!!')

    updates_netcool = []
    netcool_lines = run_query('SELECT * FROM NETCOOL_FW')
    for line in netcool_lines:
        ip = line['IP_DCN']
        in_sscd = int(db.execute(f"SELECT COUNT(IP) FROM SSCD_CI_SECURITY_IP rd WHERE IP = '{ip}'").fetchone()['COUNT(IP)'])
        in_rancid = int(db.execute(f"SELECT COUNT(IP_DCN) FROM RANCID_DEVICES rd WHERE IP_DCN = '{ip}'").fetchone()['COUNT(IP_DCN)'])
        in_portal = int(db.execute(f"SELECT COUNT(IP) FROM PORTAL_SOC_FW PSF WHERE IP = '{ip}'").fetchone()['COUNT(IP)'])
        updates_netcool.append(f'UPDATE NETCOOL_FW SET IN_SSCD = {in_sscd}, IN_PORTAL = {in_portal}, IN_RANCID = {in_rancid} WHERE IP_DCN = "{ip}"')

    for update in updates_netcool:
        update_query(update)
    print('UPDATE_NETCOOL !!!')

    UPDATE_SCCD_WITH_RANCID = '''
    INSERT INTO CONSOLIDATED_FW (CONFIG_ITEM, LOCATION_ADDRESS, CUSTOMER_NAME, IP, BACKUP_STATUS, BACKUP_DATE, OS_VERSION, IN_SSCD, IN_NETCOOL, IN_PORTAL, IN_RANCID)
	SELECT
		CID,
		LOCATION_DESC,
		CUSTOMER,
		IP_DCN,
		BACKUP_STATUS,
		BACKUP_DATE,
        OSVERSION,
        IN_SSCD,
        IN_NETCOOL,
        IN_PORTAL,
        IN_RANCID
	FROM
		RANCID_DEVICES
	WHERE IN_SSCD = 0 AND IN_PORTAL = 0 AND IN_NETCOOL = 0
    '''
    update_query(UPDATE_SCCD_WITH_RANCID)
    print('UPDATE_SCCD_WITH_RANCID !!!')

    UPDATE_SCCD_WITH_PORTAL = '''
    INSERT INTO CONSOLIDATED_FW (CONFIG_ITEM, LOCATION_ADDRESS, CUSTOMER_NAME, IP, IN_SSCD, IN_NETCOOL, IN_RANCID, IN_PORTAL)
	SELECT
		CID,
		LOCATION_DESC,
		CUSTOMER,
		IP,
        IN_SSCD,
        IN_NETCOOL,
        IN_RANCID,
        IN_PORTAL
	FROM
		PORTAL_SOC_FW
	WHERE IN_SSCD = 0 AND IN_RANCID = 0 AND IN_NETCOOL = 0
    '''
    update_query(UPDATE_SCCD_WITH_PORTAL)
    print('UPDATE_SCCD_WITH_PORTAL !!!')

    UPDATE_SCCD_WITH_NETCOOL = '''
    INSERT INTO CONSOLIDATED_FW (CONFIG_ITEM, LOCATION_ADDRESS, CUSTOMER_NAME, IP, MODEL, IN_SSCD, IN_NETCOOL, IN_RANCID, IN_PORTAL)
	SELECT
		CID,
		LOCATION_DESC,
		CUSTOMER,
		IP_DCN,
        CPE_MODEL,
        IN_SSCD,
        IN_NETCOOL,
        IN_RANCID,
        IN_PORTAL
	FROM
		NETCOOL_FW
	WHERE IN_SSCD = 0 AND IN_RANCID = 0 AND IN_PORTAL = 0
    '''
    update_query(UPDATE_SCCD_WITH_NETCOOL)
    print('UPDATE_SCCD_WITH_NETCOOL !!!')

    updates_backups = []
    backup_lines = run_query('SELECT * FROM CONSOLIDATED_FW WHERE IN_RANCID > 0')
    for line in backup_lines:
        ip = line['IP']
        backup_status = line['BACKUP_STATUS']
        backup_date = line['BACKUP_DATE']
        if backup_status.find('con') >= 0:
            query = db.execute(f'SELECT OSVERSION FROM RANCID_DEVICES WHERE IP_DCN = "{ip}"').fetchone()
            if query != None:
                os_version = query['OSVERSION']
                updates_backups.append(f'UPDATE CONSOLIDATED_FW SET OS_VERSION = "{os_version}" WHERE IP = "{ip}"')
        elif backup_status.find('act') >= 0 and backup_date.find('sin_fecha') <0 :
            delta1 = datetime.strptime(backup_date, '%b_%d_%Y')
            delta2 = datetime.now() - timedelta(days=15)
            delta = int((delta2 - delta1).days)
            if delta <= 15:
                query = db.execute(f'SELECT OSVERSION FROM RANCID_DEVICES WHERE IP_DCN = "{ip}"').fetchone()
                if query != None:
                    os_version = query['OSVERSION']
                    updates_backups.append(f'UPDATE CONSOLIDATED_FW SET OS_VERSION = "{os_version}" WHERE IP = "{ip}"')

    for update in updates_backups:
        update_query(update)
    print('UPDATE_BACKUPS !!!')

    print(f'FINAL TIME ------------------ {datetime.now()}')
    print(f'ENLAPSED TIME ------------------ {get_elapsep_time(initial_time)} (H:M:S.ms)')


if __name__ == '__main__':
    run()