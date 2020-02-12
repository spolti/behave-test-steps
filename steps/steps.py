import subprocess
import time
import os
import requests
import logging
import select
import socket
import fcntl

from behave import then, given
from container import ExecException

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT)
if os.environ.get('CTF_WAIT_TIME'):
    TIMEOUT = int(os.environ.get('CTF_WAIT_TIME'))
else:
    TIMEOUT = 30


def _execute(command, log_output=True):
    """
    Helper method to execute a shell command and redirect the logs to logger
    with proper log level.
    """

    logging.debug("Executing '%s' command..." % command)

    try:
        proc = subprocess.Popen(command, shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        levels = {
            proc.stdout: logging.DEBUG,
            proc.stderr: logging.ERROR
        }

        fcntl.fcntl(
            proc.stderr.fileno(),
            fcntl.F_SETFL,
            fcntl.fcntl(proc.stderr.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,
        )

        fcntl.fcntl(
            proc.stdout.fileno(),
            fcntl.F_SETFL,
            fcntl.fcntl(proc.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,
        )

        if log_output:
            out = ""

            while proc.poll() is None:
                readx = select.select([proc.stdout, proc.stderr], [], [])[0]
                for output in readx:
                    line = output.readline()[:-1]
                    
                    if isinstance(line, bytes):
                        line = line.decode("utf-8")

                    out += "%s\n" % line
                    logging.log(levels[output], line)

        retcode = proc.wait()

        if retcode is not 0:
            logging.error(
                "Command '%s' returned code was %s, check logs" % (command, retcode))
            return False

    except subprocess.CalledProcessError:
        logging.error("Command '%s' failed, check logs" % command)
        return False

    if log_output:
        return out
    else:
        return True


@then(u'check that page is not served')
def check_page_is_not_served(context):
    # set defaults
    port = 80
    wait = TIMEOUT
    timeout = 0.5
    expected_status_code = 200
    path = '/'
    expected_phrase = None
    username = None
    password = None
    request_method = 'GET'
    content_type = None
    request_body = None
    # adjust defaults from user table
    for row in context.table:
        if row['property'] == 'port':
            port = row['value']
        if row['property'] == 'expected_status_code':
            expected_status_code = int(row['value'])
        if row['property'] == 'wait':
            wait = int(row['value'])
        if row['property'] == 'timeout':
            timeout = row['value']
        if row['property'] == 'expected_phrase':
            expected_phrase = row['value']
        if row['property'] == 'path':
            path = row['value']
        if row['property'] == 'username':
            username = row['value']
        if row['property'] == 'password':
            password = row['value']
        if row['property'] == 'request_method':
            request_method = row['value']
        if row['property'] == 'content_type':
            content_type = row['value']
        if row['property'] == 'request_body':
            request_body = row['value']
    try:
        handle_request(context, port, wait, timeout, expected_status_code,
                       path, expected_phrase, username, password, request_method, content_type, request_body)
    except:
        return True
    raise Exception("Page was served")

@then(u'check that page is served')
def check_page_is_served(context):
    # set defaults
    port = 80
    wait = TIMEOUT
    timeout = 0.5
    expected_status_code = 200
    path = '/'
    expected_phrase = None
    username = None
    password = None
    request_method = 'GET'
    content_type = None
    request_body = None
    # adjust defaults from user table
    for row in context.table:
        if row['property'] == 'port':
            port = row['value']
        if row['property'] == 'expected_status_code':
            expected_status_code = int(row['value'])
        if row['property'] == 'wait':
            wait = int(row['value'])
        if row['property'] == 'timeout':
            timeout = row['value']
        if row['property'] == 'expected_phrase':
            expected_phrase = row['value']
        if row['property'] == 'path':
            path = row['value']
        if row['property'] == 'username':
            username = row['value']
        if row['property'] == 'password':
            password = row['value']
        if row['property'] == 'request_method':
            request_method = row['value']
        if row['property'] == 'content_type':
            content_type = row['value']
        if row['property'] == 'request_body':
            request_body = row['value']
    handle_request(context, port, wait, timeout, expected_status_code,
                   path, expected_phrase, username, password, request_method, content_type, request_body)


def handle_request(context, port, wait, timeout, expected_status_code, path, expected_phrase, username, password, request_method, content_type, request_body):
    logging.info("Checking if the container is returning status code %s on port %s" % (
        expected_status_code, port))

    start_time = time.time()
    ip = context.containers[-1].ip_address
    latest_status_code = 0
    auth=None
    headers=None
    if (username != None) or (password != None):
        auth=(username, password)

    if content_type != None:
        headers={'Content-type': content_type}

    while time.time() < start_time + wait:
        try:
            if request_method == 'GET':
                response = requests.get('http://%s:%s%s' % (ip, port, path),
                                        timeout=timeout, stream=False, auth=auth)
            elif request_method == 'POST':
                response = requests.post('http://%s:%s%s' % (ip, port, path),
                                         timeout=timeout, stream=False, auth=auth, headers=headers, data=request_body)
        except Exception as ex:
            # Logging as warning, bcause this does not neccessarily means
            # something bad. For example the server did not boot yet.
            logging.warn("Exception caught: %s" % repr(ex))
        else:
            latest_status_code = response.status_code
            logging.info("Response code from the container on port %s: %s (expected: %s)" % (
                port, latest_status_code, expected_status_code))
            if latest_status_code == expected_status_code:
                if not expected_phrase:
                    # The expected_phrase parameter was not set
                    return True

                if expected_phrase in response.text:
                    # The expected_phrase parameter was found in the body
                    logging.info(
                        "Document body contains the '%s' phrase!" % expected_phrase)
                    return True
                else:
                    # The phrase was not found in the response
                    raise Exception("Failure! Correct status code received but the document body does not contain the '%s' phrase!" % expected_phrase,
                                    "Received body:\n%s" % response.text)  # XXX: better diagnostics

        time.sleep(1)
    # XXX: better diagnostics
    raise Exception("handle_request failed", expected_status_code)


@then(u'check that port {port} is open')
def check_port_open(context, port):
    start_time = time.time()

    ip = context.containers[-1].ip_address
    logging.info("connecting to %s port %s" % (ip, port))
    while time.time() < start_time + TIMEOUT:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((ip, int(port)))
            s.close()
            return True
        except Exception as ex:
            logging.debug("not connected yes %s" % ex)
        time.sleep(1)
    raise Exception("Port %s is not open" % port)


@then(u'file {file_name} should exist')
@then(u'file {file_name} should exist and be a {file_type}')
# TODO: @then(u'file {file_name} should exist and have {permission} permissions')
def check_file_exists(context, file_name, file_type=None):
    container = context.containers[-1]

    try:
        container.execute("test -e %s" % file_name)
    except ExecException as ex:
        logging.error(ex.output)
        raise Exception("File %s does not exist" % file_name)

    if file_type:
        if file_type == "directory":
            try:
                container.execute("test -d %s" % file_name)
            except ExecException as e:
                logging.error(e.output)
                raise Exception("File %s is not a directory" % file_name)
        elif file_type == "symlink":
            try:
                container.execute("test -L %s" % file_name)
            except ExecException as e:
                logging.error(e.output)
                raise Exception("File %s is not a symlink" % file_name)

    return True


@then(u'file {file_name} should not exist')
def check_file_not_exists(context, file_name):
    container = context.containers[-1]

    try:
        container.execute("test -e %s" % file_name)
    except:
        return True

    raise Exception("File %s exists" % file_name)


@then(u'files at {path} should have count of {count}')
def check_file_count(context, path, count):
    container = context.containers[-1]
    try:
        ls = container.execute(cmd="ls -1 %s" % path)
        file_count = len(ls.splitlines())
        target_count = int(count)
        if file_count != target_count:
            raise Exception("Incorrect file count in the %s directory: expected %s files, found %s" % (
                path, target_count, file_count))
    except Exception as e:
        logging.exception(e)
        raise Exception("Failed to count files at path %s" % path)

    return True


@given(u'define variable')
def step_impl(context):
    for row in context.table:
        context.variables[row['variable']] = row['value']
