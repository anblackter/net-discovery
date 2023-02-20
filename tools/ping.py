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
    lines = run_query("SELECT * FROM SSCD_CI_SECURITY_IP WHERE SPEC_VALUE REGEXP '([0-9]{1,3}\.){3}[0-9]{1,3}'")
    counter = 0
    ip_list = []
    for line in lines:
        counter += 1
        line_id = line['CONFIG_ITEM_ID']
        ip = re.search(r"([0-9]{1,3}\.){3}[0-9]{1,3}",line['SPEC_VALUE']).group(0)
        update_query(f'UPDATE SSCD_CI_SECURITY_IP SET IP = "{ip}" WHERE CONFIG_ITEM_ID = {line_id}')
        ip_list.append(ip)
        # if counter > 9:
        #     break
    # print(ip_list)

    updates = []

    def run_ping(ip, timeout=2):
        with os.popen(f"ping {ip} -c 2 -w {timeout}") as ping:
            return ping.read()

    with ThreadPoolExecutor(max_workers=5) as executor:
        ping_answer = {executor.submit(run_ping, ip, 2): ip for ip in ip_list}
        for future in as_completed(ping_answer):
            ip = ping_answer[future]
            try:
                answer = future.result()
                data = re.search(r"(\d)(\sreceived)", answer).group(1)
            except Exception as exc:
                print('%r generated an exception: %s' % (ip, exc))
            else:
                print('%r answer is %s packets' % (ip, data))
                updates.append(f'UPDATE SSCD_CI_SECURITY_IP SET ANSWER_PING = {data} WHERE IP = "{ip}"')

    for update in updates:
        update_query(update)
    print(f'FINAL TIME ------------------ {datetime.now()}')
    print(f'ENLAPSED TIME ------------------ {get_elapsep_time(initial_time)} (H:M:S.ms)')

if __name__ == '__main__':
    run()