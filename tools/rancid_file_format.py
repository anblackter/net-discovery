import os
import re

class FileFormat():
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
                elif line.endswith('####') != True and line != '':
                    try:
                        cid = re.findall(
                            r"(?:[0-9]{5}[A-Z]{2})|(?:[0-9]{7}[A-Z]{2})|(?:[0-9]{8}[A-Z]{2})|(?:[0-9]{10}[A-Z]{2})",
                            line.split(';')[0]
                            )[0]
                        cidnum = re.findall(r"\d+", cid)[0]
                    except:
                        cid = ''
                        cidnum = ''
                    new_line = cid + ';' + cidnum + ';' + customer + ';' + line.split(';')[0] + ';' + line.split(';')[2] + \
                        ';' + line.split(';')[3] + ';' + line.split(';')[1]
                    if new_line.split(';')[-1] == 'fortigate' and new_line.find('FIREWALL') >= 0:
                        new_file.write(new_line + '\n')
        except:
            new_file.close()


