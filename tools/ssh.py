#!/usr/bin/env python3
import os
import re
from datetime import datetime, timedelta, date
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
from db_service import run_query, update_query, get_db
from config import Credenditals
from conn_driver import GenericConnectionHandler

def get_elapsep_time(initial_time):
    step_time = datetime.now()
    diff_time = step_time - initial_time
    elapsed_time = datetime.strptime(str(diff_time), '%H:%M:%S.%f')
    return elapsed_time.strftime('%H:%M:%S.%f')

def run():
    initial_time = datetime.now()
    current_path = os.path.abspath(os.path.dirname('__file__'))
    print(f'INITIAL TIME ------------------ {initial_time}')
    lines = run_query("SELECT IP, NMAP_PORTS FROM CONSOLIDATED_FW \
        WHERE NMAP_PORTS != '' AND NMAP_PORTS IS NOT NULL AND OS_VERSION IS NULL OR OS_VERSION = ''")
    counter = 0
    updates = []
    ip_port_list = []

    for line in lines:
        ip = line['IP']
        nmap_ports = line['NMAP_PORTS']
        for nmap_port in nmap_ports[:-1].split(','):
            service = nmap_port.split('_')[1]
            if service.find('ssh') >= 0 or service.find('http') < 0:
                port = nmap_port.split('_')[0]
                break
            else:
                port = ''
        if port != '':
            ip_port_list.append(f'{ip}_{port}')

    print(f' ((( {len(ip_port_list)} ))) Firewalls will be try to login and get system info ')

    def run_ssh(ip_port):
        ip = ip_port.split('_')[0]
        port = ip_port.split('_')[1]
        firewall = {
                'vendor' : 'fortinet',
                'hostname' : ip,
                'credential_list' : Credenditals.CRED_LIST_FW_2,
                'port' : port,
                'session_log' : current_path + '/logs/ssh/' + ip
            }
        fw = GenericConnectionHandler(**firewall)
        if fw.net_connect != None:
            output = fw.run_command('get system status')
            fw.net_connect.disconnect()
            return output
        else:
            return fw

    with ThreadPoolExecutor(max_workers=50) as executor:
        ssh_answer = {executor.submit(run_ssh, ip_port): ip_port for ip_port in ip_port_list}
        for future in as_completed(ssh_answer):
            ip_port = ssh_answer[future]
            ip = ip_port.split('_')[0]
            try:
                answer = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (ip_port, exc))
                updates.append(f'UPDATE CONSOLIDATED_FW SET LOGIN_MGT = "{exc}" WHERE IP = "{ip}"')
            else:
                print('%r has the following output %s' % (ip_port, answer))
                updates.append(f'UPDATE CONSOLIDATED_FW SET LOGIN_MGT = "{answer}" WHERE IP = "{ip}"')
    print(f'ENLAPSED TIME ------------------ {get_elapsep_time(initial_time)} (H:M:S.ms)')
    for update in updates:
        update_query(update)

    updates_host_sn_ver = []
    db = get_db()
    for ip_port in ip_port_list:
        ip = ip_port.split('_')[0]
        query = db.execute(f'SELECT LOGIN_MGT FROM CONSOLIDATED_FW WHERE IP = "{ip}"').fetchone()
        login_mgt = query['LOGIN_MGT']
        try:
            # model_match = re.findall(r"(\S+ersion:|\S+latfo\S+\s+\S+\s+\S+ame\s+:)(\s)(\S+)(\s)(\S+)", login_mgt)
            # model = model_match[0][2]
            version_match = re.findall(r"(\S+ersion:|\S+ersion\s+:)(\s)(\S+\s\S+\s+)", login_mgt)
            version = version_match[0][2]
            serial_match = re.findall(r"(\S+eria\S+umber:|\S+erial\s\S+umber\s+:)(\s)(\S+)", login_mgt)
            serial = serial_match[0][2]
            hostname_match = re.findall(r"(\S+ostname:|\S+ostname\s+:)(\s)(\S+)", login_mgt)
            hostname = hostname_match[0][2]
        except Exception as e:
            print(f'Error with ip {ip} --> {e}')
        else:
            print(f"ip {ip} -- version {version} -- serial {serial} -- hostname {hostname}")
            updates_host_sn_ver.append(f'UPDATE CONSOLIDATED_FW SET HOSTNAME = "{hostname}", \
                SN = "{serial}", OS_VERSION = "{version}" WHERE IP = "{ip}"')
    for update in updates_host_sn_ver:
        update_query(update)

    print(f'FINAL TIME ------------------ {datetime.now()}')
    print(f'ELAPSED TIME ------------------ {get_elapsep_time(initial_time)} (H:M:S.ms)')

if __name__ == '__main__':
    run()