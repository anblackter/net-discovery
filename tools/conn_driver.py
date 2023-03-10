
##FORTIGATEAPI
# __author__ = "James Simpson"
# __copyright__ = "Copyright 2017, James Simpson"
# __license__ = "MIT"
# __version__ = "0.3.0"

import io
import re
import time
import logging
from typing import Optional, List, Dict, Any

import paramiko
from netmiko import log, ConnectHandler, NetmikoAuthenticationException, NetMikoTimeoutException, NetmikoBaseException
from netmiko.session_log import SessionLog


import requests
import logging

from requests.exceptions import HTTPError
from urllib3.exceptions import InsecureRequestWarning
# from requests.packages.urllib3.exceptions import InsecureRequestWarning

class WEBError(HTTPError):
    def __init__(self):
        super().__init__('Error_Invalid_credentials')

class AuthError(paramiko.ssh_exception.AuthenticationException):
    def __init__(self):
        super().__init__('Error_Invalid_credentials')

class ConnError(paramiko.ssh_exception.NoValidConnectionsError):
    def __init__(self):
        super().__init__('Error_Connection_Error')

class TimeError(NetMikoTimeoutException):
    def __init__(self):
        super().__init__('Error_Timeout_Error')

class BaseError(NetmikoBaseException):
    def __init__(self):
        super().__init__('Error_Base_Error')

# Logging filter for #2597
class SecretsFilter(logging.Filter):
    def __init__(self, no_log: Optional[Dict[Any, str]] = None) -> None:
        self.no_log = no_log

    def filter(self, record: logging.LogRecord) -> bool:
        """Removes secrets (no_log) from messages"""
        if self.no_log:
            for hidden_data in self.no_log.values():
                record.msg = record.msg.replace(hidden_data, "********")
        return True

class S300ConnectHandler():
    """
    Connection Handler for Cisco SG3xx devices, base on Daniel Muñoz Script
    """
    alldata = ''

    def __init__(
        self,
        hostname : str,
        username : str = None,
        password : str = None,
        credential_list : List[List[str]] = None,
        port : Optional[int] = 22,
        timeout : Optional[int] = 10,
        delay : Optional[int] = 2,
        session_log : Optional[SessionLog] = None,
        session_log_record_writes: bool = False,
        session_log_file_mode: str = "write"
    ):
        """
        Initialize attributes for establishing connection to target device.

        :param hostname: IP or Hostname of target device.

        :param username: Username to authenticate against target device if
                required.

        :param password: Password to authenticate against target device if
                required.

        :param credential_list: list of 3 pairs of [username, password] for try to login

        :param port: The destination port used to connect to the target
                device.

        :param timeout: Connection timeout.

        :param delay: Set a delay for send commands.

        :param session_log: File path or BufferedIOBase subclass object to write the session log to.

        :param session_log_record_writes: The session log generally only records channel reads due
                to eliminate command duplication due to command echo. You can enable this if you
                want to record both channel reads and channel writes in the log (default: False).

        :param session_log_file_mode: "write" or "append" for session_log file mode
                (default: "write")
        """
        super().__init__
        self.hostname = hostname
        self.username = username
        self.password = password

        self.list_cred = [] if credential_list is None else credential_list
        if username and password:
            self.list_cred.append([username, password])

        self.port = port
        self.timeout = timeout
        self.delay = delay

        # prevent logging secret data
        no_log = {}
        if self.password:
            no_log["password"] = self.password
        log.addFilter(SecretsFilter(no_log=no_log))


        if session_log is not None:
            if isinstance(session_log, str):
                # If session_log is a string, open a file corresponding to string name.
                self.session_log = SessionLog(
                    file_name=session_log,
                    file_mode=session_log_file_mode,
                    no_log=no_log,
                    record_writes=session_log_record_writes,
                )
                self.session_log.open()
            elif isinstance(session_log, io.BufferedIOBase):
                # In-memory buffer or an already open file handle
                self.session_log = SessionLog(
                    buffered_io=session_log,
                    no_log=no_log,
                    record_writes=session_log_record_writes,
                )
            else:
                raise ValueError(
                    "session_log must be a path to a file, a file handle, "
                    "or a BufferedIOBase subclass."
                )
        self.prompt = ''
        self.try_auth_none_login()

    def __del__(self):
        self.transport.close()
        if self.session_log:
            self.session_log.close()


    def auth_none_connect(self):
        self.transport = paramiko.Transport((self.hostname, 22))
        self.transport.start_client(timeout=self.timeout)
        try:
            self.transport.auth_none('admin')
            print('auth_none success!')
            self.shell = self.transport.open_session()
            self.shell.get_pty()
            self.shell.invoke_shell()
        except paramiko.ssh_exception.BadAuthenticationType:
            print('auth_none rejected!')
            self.transport = None
            return False

    def try_auth_none_login(self, connection_try : int = 1, output : str = None):
        self.auth_none_connect()
        if len(self.list_cred) > 0:
            print(f'trying credential {connection_try}')
            output = self.receive_data() if output is None else output
            if re.search(r'user\ ?name\ ?:\ *$', output,re.IGNORECASE):
                print('user_sent') #, list_cred[0][0])
                output = self.send_command(self.list_cred[0][0])
            # print(f'---------------------{output}---------------------')
            if re.search(r'password\ ?:\ *$', output, re.IGNORECASE):
                print('password_sent') #,list_cred[0][1])
                output = self.send_command(self.list_cred[0][1])
            else:
                print('no password?', output)
                raise AuthError

            if re.search(r'password\ ?:\ *$', output, re.IGNORECASE) \
                    or re.search(r'user\ ?name\ ?:\ *$', output,re.IGNORECASE):
                return self.try_auth_none_login(connection_try + 1, output=output)
            else:
                time.sleep(self.timeout)
                return True
        elif len(self.list_cred) == 0:
            raise AuthError

    def receive_data(self):
        alldata = ''
        alldata += self.shell.recv(1024).decode()
        output = re.sub('\x1b.*?m', '', alldata)
        self.session_log.write(output)
        return output

    def send_command(self, command : str = ''):
        self.shell.send(command + '\n')
        time.sleep(self.delay)
        output = self.prompt + command + '\n'
        output += self.receive_data()
        if output.startswith(command):
            output = output[len(command):]
        return output

    def get_prompt(self):
        if self.shell:
            out = self.send_command('')
            out += self.send_command('')
            options = re.findall(r'\n(.*)$', out)
            if len(options) > 0:
                self.prompt = options[-1]
                return self.prompt

class GenericConnectionHandler():
    """
    Connection Handler for Generic devices, base on Netmiko
    """
    alldata = ''

    def __init__(
        self,
        hostname : str,
        vendor : str,
        username : str = None,
        password : str = None,
        credential_list : List[List[str]] = None,
        port : Optional[int] = 22,
        banner_timeout : Optional[int] = 200,
        conn_timeout : Optional[int] = 200,
        delay : Optional[int] = 4,
        session_log : Optional[str] = None,
        session_log_record_writes: bool = True,
        session_log_file_mode: str = "append"
    ):
        """
        Initialize attributes for establishing connection to target device.

        :param hostname: IP or Hostname of target device.

        :param vendor: Vendor of device (sg3xx, cisco, juniper, fortinet or versa)

        :param username: Username to authenticate against target device if
                required.

        :param password: Password to authenticate against target device if
                required.

        :param credential_list: list of 3 pairs of [username, password] for try to login

        :param port: The destination port used to connect to the target
                device.

        :param banner_timeout: Set a timeout to wait for the SSH banner (pass to Paramiko).

        :param conn_timeout: Set a timeout to wait for the SSH connection.

        :param delay: Set a delay for send commands.

        :param session_log: File path or BufferedIOBase subclass object to write the session log to.

        :param session_log_record_writes: The session log generally only records channel reads due
                to eliminate command duplication due to command echo. You can enable this if you
                want to record both channel reads and channel writes in the log (default: False).

        :param session_log_file_mode: "write" or "append" for session_log file mode
                (default: "write")
        """
        super().__init__
        self.hostname = hostname
        self.vendor = vendor
        self.username = username
        self.password = password
        self.port = port
        self.banner_timeout = banner_timeout
        self.conn_timeout = conn_timeout
        self.delay = delay
        self.session_log = session_log
        self.session_log_record_writes = session_log_record_writes
        self.session_log_file_mode = session_log_file_mode
        self.net_connect = None

        self.list_cred = [] if credential_list is None else credential_list
        if username and password:
            self.list_cred.append([username, password])

        self.try_auth_login(list_cred = self.list_cred)

    def __del__(self):
        if self.net_connect:
            self.net_connect.disconnect()

    def try_auth_login(self, list_cred : List[List[str]] = None, connection_try : int = 1):
        if len(list_cred) > 0:
            device = {
                'device_type' : self.vendor,
                'host' : self.hostname,
                'username' : list_cred[0][0],
                'password' : list_cred[0][1],
                'port' : self.port,
                'session_log' : self.session_log,
                'session_log_record_writes' : self.session_log_record_writes,
                'session_log_file_mode':  self.session_log_file_mode,
                'global_delay_factor' : self.delay,
                'banner_timeout' : self.banner_timeout,
                'conn_timeout' : self.conn_timeout
            }
            try:
                self.net_connect = ConnectHandler(**device)
            except NetmikoAuthenticationException as e:
                return self.try_auth_login(list_cred[1:], connection_try = connection_try + 1)
            except NetMikoTimeoutException as e:
                # print(f'\n ______________________ NetMikoTimeoutException with {self.hostname} --> \n {e} \n ______________________')
                raise TimeError
            except NetmikoBaseException as e:
                # print(f'\n ______________________ NetmikoBaseException with {self.hostname}--> \n {e} \n ______________________')
                raise BaseError
        else:
            # print(f'\n ______________________ No more credentials to try  with {self.hostname} \n ______________________')
            raise AuthError


    def run_command(self, command):
        time.sleep(self.delay) 
        output = self.net_connect.send_command(command)
        return output


class FortiGateAPI:
    def __init__(
            self,
            hostname : str,
            username : str = None,
            password : str = None,
            credential_list : List[List[str]] = None,
            timeout : Optional[int] = 10,
            vdom : Optional[str] = "root",
            port : Optional[int] = 9443,
            verify : Optional[bool] = False
            ):
        """
        Initialize attributes for establishing RESTAPI connection to target device.

        :param hostname: IP or Hostname of target device.

        :param username: Username to authenticate against target device if
                required.

        :param password: Password to authenticate against target device if
                required.

        :param credential_list: list of 3 pairs of [username, password] for try to login

        :param port: The destination port used to connect to the target
                device.

        :param timeout: Set a timeout to wait for the API connection.

        :param delay: Set a delay for send commands.

        :param vdom: Specify vdom, Default root.

        :param verify: Verify SSL certificates. Default False

        """
        super().__init__
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.urlbase = "https://{hostname}:{port}/".format(hostname=self.hostname,port=self.port)
        self.timeout = timeout
        self.vdom = vdom
        self.verify = verify

        self.list_cred = [] if credential_list is None else credential_list
        if username and password:
            self.list_cred.append([username, password])
        self.session = None

        self.login(list_cred = self.list_cred)

    # Login / Logout Handlers
    def login(self, list_cred : List[List[str]] = None, connection_try : int = 1):
        """
        Log in to FortiGate with info provided in during class instantiation


        :return: Open Session
        """
        if len(list_cred) > 0:
            self.session = requests.session()
            if not self.verify:
                # Disable requests' warnings for insecure connections
                requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            url = self.urlbase + 'logincheck'

            # Login
            self.session.post(url,
                        data='username={username}&secretkey={password}'.format(username=list_cred[0][0], password=list_cred[0][1]),
                        verify=self.verify,
                        timeout=self.timeout)

            # Get CSRF token from cookies, add to headers
            for cookie in self.session.cookies:
                if cookie.name == 'ccsrftoken':
                    csrftoken = cookie.value[1:-1]  # strip quotes
                    self.session.headers.update({'X-CSRFTOKEN': csrftoken})

            # Check whether login was successful
            self.login_check = self.session.get(self.urlbase + "api/v2/cmdb/system/vdom")
            try:
                self.login_check.raise_for_status()
            except HTTPError as e:
                return self.login(list_cred[1:], connection_try = connection_try + 1)
            except Exception:
                return e
            else:
                return self.session
        else:
            raise WEBError

    def logout(self, session):
        """
        Log out of device

        :param session: Session created by login method

        :return: None
        """
        url = self.urlbase + 'logout'
        session.get(url, verify=self.verify, timeout=self.timeout)
        logging.info("Session logged out.")

    # General Logic Methods
    def does_exist(self, object_url):
        """
        GET URL to assert whether it exists within the firewall

        :param object_url: Object to locate

        :return: Bool - True if exists, False if not
        """
        session = self.login()
        request = session.get(object_url, verify=self.verify, timeout=self.timeout, params='vdom='+self.vdom)
        self.logout(session)
        if request.status_code == 200:
            return True
        else:
            return False

    # API Interaction Methods
    def get(self, url):
        """
        Perform GET operation on provided URL

        :param url: Target of GET operation

        :return: Request result if successful (type list), HTTP status code otherwise (type int)
        """
        request = self.session.get(url, verify=self.verify, timeout=self.timeout, params='vdom='+self.vdom)
        self.logout(self.session)
        if 200 <= request.status_code < 400:
            return request.json()
        else:
            return request.status_code

    def put(self, url, data):
        """
        Perform PUT operation on provided URL

        :param url: Target of PUT operation
        :param data: JSON data. MUST be a correctly formatted string. e.g. "{'key': 'value'}"

        :return: HTTP status code returned from PUT operation
        """
        session = self.login(list_cred = self.list_cred)
        result = session.put(url, data=data, verify=self.verify, timeout=self.timeout, params='vdom='+self.vdom).status_code
        self.logout(session)
        return result

    def post(self, url, data):
        """
        Perform POST operation on provided URL

        :param url: Target of POST operation
        :param data: JSON data. MUST be a correctly formatted string. e.g. "{'key': 'value'}"

        :return: HTTP status code returned from POST operation
        """
        session = self.login(list_cred = self.list_cred)
        result = session.post(url, data=data, verify=self.verify, timeout=self.timeout, params='vdom='+self.vdom).status_code
        self.logout(session)
        return result

    def delete(self, url):
        """
        Perform DELETE operation on provided URL

        :param url: Target of DELETE operation

        :return: HTTP status code returned from DELETE operation
        """
        session = self.login(list_cred = self.list_cred)
        result = session.delete(url, verify=self.verify, timeout=self.timeout, params='vdom='+self.vdom).status_code
        self.logout(session)
        return result
