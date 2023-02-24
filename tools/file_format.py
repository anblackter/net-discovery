import os
import re

class RancidFileFormat():
    def __init__(self, file : str = 'resultado_final.txt'):
        self.file = file
        self.current_path = os.path.abspath(os.path.dirname('__file__')) + '/data/'
        self.read_file()

    def read_file(self):
        with open(self.current_path + self.file) as file:
            self.data = file.read().splitlines()
        # self.get_info()

    def get_info(self):
        lines = self.data
        #HEADER --> 'CID;CIDNUM;CUSTOMER;LOCATION_DESC;IP_DCN;OSVERSION;VENDOR'
        new_file = open(self.current_path + 'rancid_db.csv', 'w+')
        new_line = ''
        customer = ''
        try:
            for line in lines:
                if line.startswith('#### '):
                    customer = line.replace('#### ', '')
                elif line.endswith('####') != True and line != '' and line.find('fortigate') >= 0 and line.find('FIREWALL') >= 0:
                    try:
                        cid = re.findall(
                            r"(?:[0-9]{5}[A-Z]{2})|(?:[0-9]{7}[A-Z]{2})|(?:[0-9]{8}[A-Z]{2})|(?:[0-9]{10}[A-Z]{2})",
                            line.split(';')[0]
                            )[0]
                        cidnum = re.findall(r"\d+", cid)[0]
                    except:
                        cid = ''
                        cidnum = ''
                    ip = line.split(';')[2]
                    cmd = "grep " + "'\<" + ip + "\\>' " + self.current_path +  "resumen_modelo.txt | awk -F';' '{print $5}'"
                    # print(cmd)
                    output = os.popen(cmd).read()
                    try:
                        backup_status = output.splitlines()[0]
                    except:
                        backup_status = output.replace('\n','')

                    cmd = "grep " + "'\<" + ip + "\\>' " + self.current_path +  "resumen_modelo.txt | awk -F';' '{print $6}'"
                    # print(cmd)
                    output = os.popen(cmd).read()
                    try:
                        backup_date = output.splitlines()[0]
                    except:
                        backup_date = output.replace('\n','')

                    new_line = cid + ';' + cidnum + ';' + customer + ';' + line.split(';')[0] + ';' + line.split(';')[2] + \
                        ';' + line.split(';')[3] + ';' + backup_status + ';' + backup_date + ';' + line.split(';')[1]
                    # if new_line.split(';')[-1] == 'fortigate' and new_line.find('FIREWALL') >= 0:
                    new_file.write(new_line + '\n')
        except Exception as e:
            print(e)
            new_file.close()

class PortalFileFormat():
    def __init__(self, file : str = 'portal_db_base.csv'):
        self.file = file
        self.current_path = os.path.abspath(os.path.dirname('__file__')) + '/data/'
        self.read_file()

    def read_file(self):
        with open(self.current_path + self.file) as file:
            self.data = file.read().splitlines()
        # self.get_info()

    def get_info(self):
        lines = self.data
        #HEADER --> 'CID;CUSTOMER;LOCATION_DESC;IP_DCN;MGT_PORT;SN;OSVERSION;LIC_EXPIRATION'
        new_file = open(self.current_path + 'portal_db_expanded.csv', 'w+')
        try:
            for line in lines:
                cid = line.split(';')[0]
                customer = line.split(';')[1]
                location = line.split(';')[2]
                try :
                    ip_dcn = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", line.split(';')[3])[0]
                except:
                    ip_dcn = line.split(';')[3]
                try:
                    ip_public = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", line.split(';')[4])[0]
                except:
                    ip_public = line.split(';')[4]
                # print(ip_dcn)
                # print(ip_public)
                mgt_port = line.split(';')[5]
                sn = line.split(';')[6]
                os_version = line.split(';')[7]
                lic = line.split(';')[8]
                if ip_dcn != ip_public:
                    new_line1 = cid + ';' + customer + ';' + location + ';' + ip_dcn + ';' + mgt_port + ';' + sn + ';' + os_version + ';' + lic
                    new_line2 = cid + ';' + customer + ';' + location + ';' + ip_public + ';' + mgt_port + ';' + sn + ';' + os_version + ';' + lic
                    new_file.write(new_line1 + '\n')
                    new_file.write(new_line2 + '\n')
                else:
                    new_line1 = cid + ';' + customer + ';' + location + ';' + ip_dcn + ';' + mgt_port + ';' + sn + ';' + os_version + ';' + lic
                    new_file.write(new_line1 + '\n')

        except:
            new_file.close()

class PortalFileDepuration():
    def __init__(self, file : str = 'portal_db_expanded.csv'):
        self.file = file
        self.current_path = os.path.abspath(os.path.dirname('__file__')) + '/data/'
        self.read_file()

    def read_file(self):
        with open(self.current_path + self.file) as file:
            self.data = file.read().splitlines()
        # self.get_info()

    def depurate(self):
        lines = self.data
        new_file = open(self.current_path + 'portal_db_transition.csv', 'w+')
        #HEADER --> 'CID;CUSTOMER;LOCATION_DESC;IP_DCN;MGT_PORT;SN;OSVERSION;LIC_EXPIRATION'

        for line in lines:
            try:
                re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", line.split(';')[3])[0]
            except:
                pass
            else:
                new_file.write(line + '\n')

        new_file.close()



