#!/usr/bin/env python3
import os
import re
from datetime import datetime
from config import Credenditals
from concurrent.futures import ThreadPoolExecutor, as_completed
from db_service import run_query, update_query, get_db
from conn_driver import FortiGateAPI

def get_elapsep_time(initial_time):
    step_time = datetime.now()
    diff_time = step_time - initial_time
    elapsed_time = datetime.strptime(str(diff_time), '%H:%M:%S.%f')
    return elapsed_time.strftime('%H:%M:%S.%f')

def run():
    initial_time = datetime.now()
    print(f'INITIAL TIME ------------------ {initial_time}')
    lines = run_query("SELECT IP, NMAP_PORTS FROM CONSOLIDATED_FW \
        WHERE NMAP_PORTS != '' AND NMAP_PORTS IS NOT NULL AND OS_VERSION IS NULL OR OS_VERSION = 'Sin_informacion'")

    updates_host_sn_ver = []
    ip_port_list = []
    for line in lines:
        ip = line['IP']
        nmap_ports = line['NMAP_PORTS']
        for nmap_port in nmap_ports[:-1].split(','):
            service = nmap_port.split('_')[1]
            if service.find('https') >= 0:
                port = nmap_port.split('_')[0]
                break
            else:
                port = ''
        if port != '':
            ip_port_list.append(f'{ip}_{port}')

    def run_fortigate_api(ip_port):
        ip = ip_port.split('_')[0]
        port = ip_port.split('_')[1]
        firewall = {
                'hostname' : ip,
                'credential_list' : Credenditals.CRED_LIST_FW_2,
                'port' : port
            }
        fw = FortiGateAPI(**firewall)
        response = fw.get(f'https://{ip}:{port}/api/v2/cmdb/system/global')
        if response != None:
            return response
        else:
            return fw

    with ThreadPoolExecutor(max_workers=50) as executor:
        api_answer = {executor.submit(run_fortigate_api, ip_port): ip_port for ip_port in ip_port_list}
        for future in as_completed(api_answer):
            ip_port = api_answer[future]
            ip = ip_port.split('_')[0]
            try:
                answer = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (ip_port, exc))
                updates_host_sn_ver.append(f'UPDATE CONSOLIDATED_FW SET LOGIN_API = "{exc}" WHERE IP = "{ip}"')
            else:
                if type(answer) == dict:
                    try:
                        hostname = answer['results']['hostname']
                        serial = answer['serial']
                        version = str(answer['version']) + ', build ' + str(answer['build'])
                    except:
                        updates_host_sn_ver.append(f'UPDATE CONSOLIDATED_FW SET LOGIN_API = "{answer}" WHERE IP = "{ip}"')
                    else:
                        print(f"ip {ip_port} -- version {version} -- serial {serial} -- hostname {hostname}")
                        updates_host_sn_ver.append(f'UPDATE CONSOLIDATED_FW SET HOSTNAME = "{hostname}", \
                            SN = "{serial}", OS_VERSION = "{version}", LOGIN_API = "{answer}" WHERE IP = "{ip}"')
                else:
                    print(f"ip {ip_port} -- answer {answer}")
                    updates_host_sn_ver.append(f'UPDATE CONSOLIDATED_FW SET LOGIN_API = "{answer}" WHERE IP = "{ip}"')
    print(f'ELAPSED TIME ------------------ {get_elapsep_time(initial_time)} (H:M:S.ms)')
    for update in updates_host_sn_ver:
        update_query(update)

    print(f'FINAL TIME ------------------ {datetime.now()}')
    print(f'ELAPSED TIME ------------------ {get_elapsep_time(initial_time)} (H:M:S.ms)')

if __name__ == '__main__':
    run()