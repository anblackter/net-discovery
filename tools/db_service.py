#!/usr/bin/env python3
import os
import sqlite3
import csv
import pandas as pd
import re

def get_db():
    DATABASE=os.path.abspath(os.path.dirname('__file__')) + '/data/net_discovery.sqlite'
    # print(DATABASE)
    db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    db.create_function('regexp', 2, lambda x, y: 1 if re.search(x,y) else 0)

    return db

def close_db(db):
    if db is not None:
        db.close()

def init_db():
    current_path = os.path.abspath(os.path.dirname('__file__'))
    print(current_path)
    os.system(f'rm {current_path}/data/net_discovery.sqlite && touch {current_path}/data/net_discovery.sqlite')
    db = get_db()

    with open(current_path + '/tools/schema.sql', 'r') as script:
        db.executescript(script.read())
        print('Script sucessfully executed!! (Database initialized)')

def populate_table(table):
    current_path = os.path.abspath(os.path.dirname('__file__'))
    db = get_db()
    cursor = db.cursor()
    if table == 'rancid':
        file_path = current_path + '/data/rancid_db.csv'
        insert_records = 'INSERT INTO RANCID_DEVICES \
        (CID, CIDNUM, CUSTOMER, LOCATION_DESC, IP_DCN, OSVERSION, BACKUP_STATUS, BACKUP_DATE, VENDOR)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
    elif table == 'cispec':
        file_path = current_path + '/data/CISPEC.csv'
        insert_records = 'INSERT INTO SSCD_CISPEC\
        (CISPECID, ALNVALUE, ASSETATTRID, CINUM, CHANGEDATE)\
            VALUES (?, ?, ?, ?, ?)'
    elif table == 'ci_security':
        file_path = current_path + '/data/ci_security.csv'
        insert_records = 'INSERT INTO SSCD_CI_SECURITY \
        (CONFIG_ITEM, CLASS_ID, CLASS_DESC, LOCATION_ID, LOCATION_DESC, LOCATION_COUNTRY,\
        LOCATION_ADDRESS, CUSTOMER_ID, CUSTOMER_NAME)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
    elif table == 'ci_security_ip_transition':
        file_path = current_path + '/data/ci_security_ip_transition.csv'
        insert_records = 'INSERT INTO SSCD_CI_SECURITY_IP_TRANSITION \
        (CONFIG_ITEM, CLASS_ID, CLASS_DESC, LOCATION_ID, LOCATION_DESC, LOCATION_COUNTRY,\
        LOCATION_ADDRESS, CUSTOMER_ID, CUSTOMER_NAME, SPEC_VALUE, SPEC_DESC)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    elif table == 'ci_security_ip':
        file_path = current_path + '/data/ci_security_ip.csv'
        insert_records = 'INSERT INTO SSCD_CI_SECURITY_IP \
        (CONFIG_ITEM, CLASS_ID, CLASS_DESC, LOCATION_ID, LOCATION_DESC, LOCATION_COUNTRY,\
        LOCATION_ADDRESS, CUSTOMER_ID, CUSTOMER_NAME, SPEC_VALUE, SPEC_DESC, IP)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        lines = run_query("SELECT * FROM SSCD_CI_SECURITY_IP_TRANSITION WHERE SPEC_VALUE REGEXP '([0-9]{1,3}\.){3}[0-9]{1,3}'")
        for line in lines:
            line_id = line['CONFIG_ITEM_ID']
            ip = re.search(r"([0-9]{1,3}\.){3}[0-9]{1,3}",line['SPEC_VALUE']).group(0)
            update_query(f'UPDATE SSCD_CI_SECURITY_IP_TRANSITION SET IP = "{ip}" WHERE CONFIG_ITEM_ID = {line_id}')
        sql_query = pd.read_sql_query('SELECT CONFIG_ITEM, CLASS_ID, CLASS_DESC, LOCATION_ID,\
            LOCATION_DESC, LOCATION_COUNTRY, LOCATION_ADDRESS, CUSTOMER_ID, CUSTOMER_NAME, \
            SPEC_VALUE, SPEC_DESC, IP FROM (SELECT * FROM SSCD_CI_SECURITY_IP_TRANSITION GROUP BY IP)',\
            con = db)
        df = pd.DataFrame(sql_query)
        df.to_csv(file_path, index = False, header=False, sep=';')
    elif table == 'soc_transition':
        file_path = current_path + '/data/portal_db_transition.csv'
        insert_records = 'INSERT INTO PORTAL_SOC_FW_TRANSITION (CID, CUSTOMER, LOCATION_DESC, IP, MGT_PORT, SN, OSVERSION, LIC_EXPIRATION)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    elif table == 'soc':
        file_path = current_path + '/data/portal_db.csv'
        insert_records = 'INSERT INTO PORTAL_SOC_FW (CID, CUSTOMER, LOCATION_DESC, IP, MGT_PORT, SN, OSVERSION, LIC_EXPIRATION)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        sql_query = pd.read_sql_query('SELECT CID, CUSTOMER, LOCATION_DESC, IP, MGT_PORT, SN, OSVERSION, LIC_EXPIRATION\
                                       FROM (SELECT * FROM PORTAL_SOC_FW_TRANSITION GROUP BY IP)',\
            con = db)
        df = pd.DataFrame(sql_query)
        df.to_csv(file_path, index = False, header=False, sep=';')
    elif table == 'netcool_transition':
        file_path = current_path + '/data/netcool_transition.csv'
        insert_records = 'INSERT INTO NETCOOL_DEVICES (IP_DCN, CUSTOMER, CID, CPE_MODEL, COUNTRY, CITY, STATE_NAME, LOCATION_DESC, DEPARTMENT)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
    elif table == 'netcool':
        file_path = current_path + '/data/netcool.csv'
        insert_records = 'INSERT INTO NETCOOL_FW (IP_DCN, CUSTOMER, CID, CPE_MODEL, COUNTRY, CITY, STATE_NAME, LOCATION_DESC, DEPARTMENT)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
        sql_query = pd.read_sql_query("SELECT IP_DCN, CUSTOMER, CID, CPE_MODEL, COUNTRY, CITY, STATE_NAME, LOCATION_DESC, DEPARTMENT\
                                       FROM (SELECT * FROM NETCOOL_DEVICES WHERE CPE_MODEL REGEXP '\Sorti')",\
            con = db)
        df = pd.DataFrame(sql_query)
        df.to_csv(file_path, index = False, header=False, sep=';')
    else:
        print('Invalid Table!!')

    # source = pd.read_csv(file_path)
    # source.to_sql('SSCD_CISPEC', db, if_exists='drop', index = False)
    source = open(file_path)
    contents = csv.reader(source, delimiter=';')
    cursor.executemany(insert_records, contents)
    db.commit()
    source.close()
    db.close()
    print(f'QUERY "{insert_records}" run sucessfully!!!')
    print(f"Table {table} Sucessfully populate!")

def update_table(table):
    if table == 'ci_security_ip':
        UPDATE_QUERY = 'UPDATE SSCD_CI_SECURITY_IP SET IN_SSCD = 1'
    elif table == 'rancid':
        UPDATE_QUERY = 'UPDATE RANCID_DEVICES SET IN_RANCID = 1'
    elif table == 'soc':
        UPDATE_QUERY = 'UPDATE PORTAL_SOC_FW SET IN_PORTAL = 1'
    elif table == 'netcool':
        UPDATE_QUERY = 'UPDATE NETCOOL_DEVICES SET IN_NETCOOL = 1'
    else:
        print('Invalid Table!!')
    update_query(UPDATE_QUERY)



def run_query(query):
    db = get_db()
    sql_query = pd.read_sql_query(query, con = db)
    df = pd.DataFrame(sql_query)
    df.to_csv(r'./data/query.csv', index = False, sep=';')

    answer = db.execute(query).fetchall()
    return answer

def update_query(query):
    db = get_db()
    db.execute(query)
    db.commit()
    # print(f'QUERY "{query}" run sucessfully!!!')

def alter_query(query):
    db = get_db()
    db.execute(query)
    # db.commit()
    # print(f'QUERY "{query}" run sucessfully!!!')
