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
        (CID, CIDNUM, CUSTOMER, LOCATION_DESC, IP_DCN, OSVERSION, VENDOR)\
            VALUES (?, ?, ?, ?, ?, ?, ?)'
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
    elif table == 'ci_security_ip':
        file_path = current_path + '/data/ci_security_ip.csv'
        insert_records = 'INSERT INTO SSCD_CI_SECURITY_IP \
        (CONFIG_ITEM, CLASS_ID, CLASS_DESC, LOCATION_ID, LOCATION_DESC, LOCATION_COUNTRY,\
        LOCATION_ADDRESS, CUSTOMER_ID, CUSTOMER_NAME, SPEC_VALUE, SPEC_DESC)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    elif table == 'soc':
        file_path = current_path + '/data/portal_db.csv'
        insert_records = 'INSERT INTO PORTAL_SOC_FW \
        (CID, CUSTOMER, LOCATION_DESC, IP_DCN, IP_PUBLIC, MGT_PORT,\
        SN, OSVERSION, LIC_EXPIRATION)\
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
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
    print(f"Table {table} Sucessfully populate!")

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
    print(f'QUERY "{query}" run sucessfully!!!')

def alter_query(query):
    db = get_db()
    db.execute(query)
    # db.commit()
    print(f'QUERY "{query}" run sucessfully!!!')
    
