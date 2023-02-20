#!/usr/bin/env python3
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from db_service import run_query, update_query

def get_elapsep_time(initial_time):
    step_time = datetime.now()
    diff_time = step_time - initial_time
    elapsed_time = datetime.strptime(str(diff_time), '%H:%M:%S.%f')
    return elapsed_time.strftime('%H:%M:%S.%f')

def run():
    initial_time = datetime.now()
    print(f'INITIAL TIME ------------------ {initial_time}')
    lines = run_query("SELECT * FROM SSCD_CI_SECURITY_IP WHERE ANSWER_PING > 0")
    counter = 0
    ip_list = []
    for line in lines:
        counter += 1
        line_id = line['CONFIG_ITEM_ID']
        ip = re.search(r"([0-9]{1,3}\.){3}[0-9]{1,3}", line['IP']).group(0)
        # update_query(f'UPDATE SSCD_CI_SECURITY_IP SET IP = "{ip}" WHERE CONFIG_ITEM_ID = {line_id}')
        ip_list.append(ip)
        # if counter > 9:
        #     break
    # print(ip_list)

    updates = []

    def run_nmap(ip):
        with os.popen(f"nmap -Pn -p 20,22,80,222,443,1322,1337,4443,9443,9444,11443,12443,17220 '{ip}'") as nmap:
            return nmap.read()

    with ThreadPoolExecutor(max_workers=5) as executor:
        nmap_answer = {executor.submit(run_nmap, ip): ip for ip in ip_list}
        for future in as_completed(nmap_answer):
            ip = nmap_answer[future]
            try:
                nmap = ''
                answer = future.result()
                # print(answer)
                matches = re.findall(r"(\d+)(\/tcp)(\s+)(\w+)(\s+)(\w+\-\w+|\w+)", answer)
                for match in matches:
                    if match[3].find('open')>= 0:
                        nmap += match[0] + '_' + match[5] + ','
                # print(nmap)
            except Exception as exc:
                print('%r generated an exception: %s' % (ip, exc))
            else:
                print('%r has ports %s open' % (ip, nmap))
                updates.append(f'UPDATE SSCD_CI_SECURITY_IP SET NMAP_PORTS = "{nmap}" WHERE IP = "{ip}"')
    # print(updates)

    for update in updates:
        update_query(update)
    print(f'FINAL TIME ------------------ {datetime.now()}')
    print(f'ENLAPSED TIME ------------------ {get_elapsep_time(initial_time)} (H:M:S.ms)')

if __name__ == '__main__':
    run()