import os
import pandas as pd
import cx_Oracle

def run():

    os.system("grep 10.254.218.74 /etc/hosts || echo 10.254.218.74 reporting-scan.corp-it.cc >> /etc/hosts")

    dsn = cx_Oracle.makedsn("reporting-scan.corp-it.cc", 1521, service_name="reporting_sccd.corp-it.cc")
    con = cx_Oracle.connect(user="CBS_SCCD_VIEWER", password="B090t45rvcCtr", dsn=dsn)

    QUERY_CI_SECURITY = '''
    SELECT
        CI.CINUM AS CONFIG_ITEM,
        CI.CLASSSTRUCTUREID AS CLASS_ID,
        C.DESCRIPTION AS CLASS_DESC,
        CI.CILOCATION AS LOCATION_ID,
        L.DESCRIPTION AS LOCATION_DESC,
        L.CG_LOCCOUNTRY AS LOCATION_COUNTRY,
        L.CG_LOCADDRESS AS LOCATION_ADDRESS,
        CI.PLUSPCUSTOMER AS CUSTOMER_ID,
        P.NAME AS CUSTOMER_NAME
    FROM
        MAXIMO.CI CI
        LEFT JOIN MAXIMO.CLASSSTRUCTURE C ON CI.CLASSSTRUCTUREID = C.CLASSSTRUCTUREID
        LEFT JOIN MAXIMO.LOCATIONS L ON CI.CILOCATION = L.LOCATION
        LEFT JOIN MAXIMO.PLUSPCUSTOMER P ON CI.PLUSPCUSTOMER = P.CUSTOMER
    WHERE
        REGEXP_LIKE(C.DESCRIPTION , '*GUARD')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*SECURITY')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*THREAT')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*FIREWALL')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*FORTI')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*ADVANCE')
        AND NOT
        REGEXP_LIKE(C.DESCRIPTION , '*ISSUE')
    '''
    QUERY_CI_SECURITY_IP = '''
    WITH SSCD_CI_SECURITY AS (
	SELECT
        CI.CINUM AS CONFIG_ITEM,
        CI.CLASSSTRUCTUREID AS CLASS_ID,
        C.DESCRIPTION AS CLASS_DESC,
        CI.CILOCATION AS LOCATION_ID,
        L.DESCRIPTION AS LOCATION_DESC,
        L.CG_LOCCOUNTRY AS LOCATION_COUNTRY,
        L.CG_LOCADDRESS AS LOCATION_ADDRESS,
        CI.PLUSPCUSTOMER AS CUSTOMER_ID,
        P.NAME AS CUSTOMER_NAME,
        C2.ALNVALUE AS SPEC_VALUE,
        C2.ASSETATTRID AS SPEC_DESC
	FROM
        MAXIMO.CI CI
        LEFT JOIN MAXIMO.CLASSSTRUCTURE C ON CI.CLASSSTRUCTUREID = C.CLASSSTRUCTUREID
        LEFT JOIN MAXIMO.LOCATIONS L ON CI.CILOCATION = L.LOCATION
        LEFT JOIN MAXIMO.PLUSPCUSTOMER P ON CI.PLUSPCUSTOMER = P.CUSTOMER
        INNER JOIN MAXIMO.CISPEC C2 ON CI.CINUM = C2.CINUM
	WHERE
        REGEXP_LIKE(C.DESCRIPTION , '*GUARD')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*SECURITY')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*THREAT')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*FIREWALL')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*FORTI')
        OR
        REGEXP_LIKE(C.DESCRIPTION , '*ADVANCE')
        AND NOT
        REGEXP_LIKE(C.DESCRIPTION , '*ISSUE')
    ) SELECT * FROM SSCD_CI_SECURITY
    WHERE
        REGEXP_LIKE(SPEC_VALUE, '([0-9]{1,3}\.){3}[0-9]{1,3}')
        AND NOT
        REGEXP_LIKE(SPEC_DESC , '*CUSTOMER|*SERVICE|*SERIAL|*DNS')
        AND NOT
        REGEXP_LIKE(SPEC_VALUE, 'NO|NA|N/A|n/a|(?:[0-9]{5}[A-Z]{2})|(?:[0-9]{7}[A-Z]{2})|(?:[0-9]{8}[A-Z]{2})|(?:[0-9]{10}[A-Z]{2})')
        AND
        SPEC_VALUE IS NOT NULL
    '''
    sql_query = pd.read_sql_query(QUERY_CI_SECURITY, con = con)
    df = pd.DataFrame(sql_query)
    df.to_csv(r'/data/ci_security.csv', index = False, header=False, sep=';')

    sql_query = pd.read_sql_query(QUERY_CI_SECURITY_IP, con = con)
    df = pd.DataFrame(sql_query)
    df.to_csv(r'/data/ci_security_ip.csv', index = False, header=False, sep=';')

if __name__ == '__main__':
    run()