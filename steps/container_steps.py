from behave import when, then, given
import time
import re
import logging
from steps import TIMEOUT
from container import Container, ExecException

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT)


@when(u'container is ready')
def container_is_started(context, pname="java"):
    container = Container(context.config.userdata['IMAGE'], name=context.scenario.name)
    container.start()
    context.containers.append(container)
    wait_for_process(context, pname)


@then(u'container log should match regex {regex}')
def log_matches_regex(context, regex, timeout=TIMEOUT):
    if not run_log_matches_regex(context, regex, timeout):
        raise Exception("Regex '%s' did not match the logs" % regex)


@then(u'container log should contain {message}')
def log_contains_msg(context, message, timeout=TIMEOUT):
    if not run_log_contains_msg(context, message, timeout):
        raise Exception("Message '%s' was not found in the logs" % message)


@then(u'container log should not contain {message}')
def log_not_contains_msg(context, message, timeout=TIMEOUT):
    """
    This will check if {message} is not available in the container
    log. It'll wait until the default timeout.
    Sometimes you want to check it only once, see
    available_log_not_contains_msg method
    """

    if run_log_contains_msg(context, message, timeout):
        raise Exception("Message '%s' was found in the logs but it shoudn't be there" % message)


@then(u'available container log should contain {message}')
def available_log_contains_msg(context, message):
    """
    This will check only *once* if the {message} is available in
    the container log.
    """

    if not run_log_contains_msg(context, message, timeout=0):
        raise Exception("Message '%s' was not found in the logs" % message)


@then(u'available container log should not contain {message}')
def available_log_not_contains_msg(context, message):
    """
    This will check only *once* if the {message} is missing in
    the container log.
    """

    if run_log_contains_msg(context, message, timeout=0):
        raise Exception("Message '%s' was found in the logs but it shoudn't be there" % message)


@given(u'container is started with env')
@when(u'container is started with env')
@when(u'container is started with env with process {pname}')
def start_container(context, pname="java"):
    env = {}
    for row in context.table:
        env[row['variable']] = row['value']
    container = Container(context.config.userdata['IMAGE'], name=context.scenario.name)
    container.start(environment=env)
    context.containers.append(container)
    wait_for_process(context, pname)


@given(u'container is started with args')
@when(u'container is started with args')
def start_container_with_args(context, pname="java"):
    kwargs = {}
    for row in context.table:
        kwargs[row['arg']] = row['value']
    container = Container(context.config.userdata['IMAGE'], name=context.scenario.name)
    container.start(**kwargs)
    context.containers.append(container)
    wait_for_process(context, pname)


@given(u'container is started with command {cmd}')
@when(u'container is started with command {cmd}')
@when(u'container {name} is started with command {cmd}')
def start_container_with_command(context, cmd, name="", pname="java"):
    """
    This will start a container with a specific command provided by the user
    Useful for container that does not have an entrypoint or does not executes nothing
    i.e. start the container with bash command eh perform some commands on the container
    """
    env = {}
    if (context.table):
        for row in context.table:
            env[row['variable']] = row['value']

    container = Container(name + context.config.userdata['IMAGE'], name=context.scenario.name)
    kwargs = {"command": cmd, "environment": env}
    container.startWithCommand(**kwargs)

    context.containers.append(container)
    wait_for_process(context, pname)


@given(u'image is built')
def image(context):
    pass


@given(u'container is started with args and env')
@when(u'container is started with args and env')
def start_container_with_args_and_env(context, pname="java"):
    kwargs = {}
    env = {}
    for row in context.table:
        if str(row['arg_env']).startswith('arg'):
            kwargs[str(row['arg_env']).replace('arg_', '')] = row['value']
        elif str(row['arg_env']).startswith('env'):
            env[str(row['arg_env']).replace('env_', '')] = row['value']
        else:
            raise Exception("Invalid argument or variable '%s', it should prefixed with 'arg' for arguments or 'env' "
                            "for variables" % row['arg_env'])
    container = Container(context.config.userdata['IMAGE'], name=context.scenario.name)
    container.start(environment=env, **kwargs)
    context.containers.append(container)
    wait_for_process(context, pname)


@given(u'container is started as uid {uid}')
@when(u'container is started as uid {uid}')
@when(u'container is started as uid {uid} with process {pname}')
def start_container(context, uid, pname="java"):
    # we get UID as string from behave, so we compare to string "0" for python3 compatibility
    if uid < "0":
        raise Exception("UID %d is negative" % uid)
    container = Container(context.config.userdata['IMAGE'], save_output=False, name=context.scenario.name)
    container.start(user=uid)
    context.containers.append(container)
    wait_for_process(context, pname)


def wait_for_process(context, pname):
    """
    Methods which runs ps in a container looking fo
    given process
    """
    start_time = time.time()
    timeout = 10
    while time.time() < start_time + timeout:
        try:
            run_command_immediately_expect_message(context, "ps -C %s" % pname, pname)
            return
        except:
            time.sleep(1)


def run_log_matches_regex(context, regex, timeout):
    """
    check the container log output against a regex. It uses
    optional timeout mechanism.
    """
    start_time = time.time()
    container = context.containers[-1]

    while True:
        logs = container.get_output().decode()
        if re.search(regex, logs, re.MULTILINE):
            logging.info("regex '%s' matched the logs" % regex)
            return True
        if time.time() > start_time + timeout:
            break
        # TODO: Add customization option for sleep time
        time.sleep(1)
    else:
        return False


def run_log_contains_msg(context, message, timeout):
    """
    Main method that handles checking the container log
    output. It's used to determine whether the message
    is found in the log or not. It uses optional timeout
    mechanism.
    """

    start_time = time.time()
    container = context.containers[-1]

    while True:
        logs = container.get_output().decode()
        if message in logs:
            logging.info("Message '%s' was found in the logs" % message)
            return True
        if time.time() > start_time + timeout:
            break
        # TODO: Add customization option for sleep time
        time.sleep(1)
    else:
        return False


@then(u'all files under {path} are writeable by current user')
def check_that_paths_are_writeable(context, path):
    container = context.containers[-1]

    user = container.execute(cmd="id -u").strip().decode()
    group = container.execute(cmd="id -g").strip().decode()

    output = container.execute(cmd="find %s ! ( ( -user %s -perm -u=w ) -o ( -group %s -perm -g=w ) ) -ls" % (path, user, group))

    if len(output) is 0:
        return True

    raise Exception("Not all files on %s path are writeable by %s user or %s group" % (path, user, group), output)


@then(u'run {cmd} in container and immediately check its output for {output_phrase}')
@then(u'run {cmd} in container and immediately check its output contains {output_phrase}')
def run_command_immediately_expect_message(context, cmd, output_phrase):
    return run_command_expect_message(context, cmd, output_phrase, 0)


@then(u'run {cmd} in container and immediately check its output does not contain {output_phrase}')
def run_command_immediately_unexpect_message(context, cmd, output_phrase):
    try:
        run_command_expect_message(context, cmd, output_phrase, 0)
    except:
        return True
    raise Exception("commmand output contains prohibited text")


@then(u'run {cmd} in container and check its output does not contain {output_phrase}')
def run_command_unexpect_message(context, cmd, output_phrase, timeout=80):
    try:
        run_command_expect_message(context, cmd, output_phrase, timeout)
    except:
        return True
    raise Exception("commmand output contains prohibited text")


@then(u'run {cmd} in container once')
def run_command_once(context, cmd):
    run_command_expect_message(context, cmd, None, timeout=0)


@then(u'run {cmd} in container and detach')
def run_command_and_detach(context, cmd):
        container = context.containers[-1]
        container.execute(cmd=cmd, detach=True)


@then(u'run {cmd} in container and check its output for {output_phrase}')
@then(u'run {cmd} in container and check its output contains {output_phrase}')
@then(u'run {cmd} in container')
def run_command_expect_message(context, cmd, output_phrase, timeout=80):
    start_time = time.time()

    container = context.containers[-1]

    # If timeout is set to 0, then we'll run the specific command only once
    if timeout == 0:
        last_output = container.execute(cmd=cmd).decode()
        if (not output_phrase) or output_phrase in last_output:
            return True
    else:
        while time.time() < start_time + timeout:
            last_output = None
            try:
                output = container.execute(cmd=cmd).decode()
                if output_phrase in output:
                    return True
            except ExecException as e:
                last_output = e.output
                time.sleep(1)
    raise Exception("Phrase '%s' was not found in the output of running the '%s' command" % (output_phrase, cmd), last_output)


@then('file {filename} should contain {phrase}')
def file_should_contain(context, filename, phrase):
    filename = context.variables.get(filename[1:], filename)
    run_command_expect_message(context, 'cat %s' % filename, phrase, timeout=10)


@then('file {filename} should not contain {phrase}')
def file_should_not_contain(context, filename, phrase):
    filename = context.variables.get(filename[1:], filename)
    run_command_unexpect_message(context, 'cat %s' % filename, phrase, timeout=10)

@then(u'inspect container')
def inspect_container(context):
    container = context.containers[-1]
    inspect = container.inspect()
    for row in context.table:
        path = row['path']
        value = row['value']

        location = inspect

        components = path.split('/')
        for component in components:
            if component and component.strip():
                try:
                    location = location[component]
                except KeyError:
                    raise Exception("Could not find path component '%s' in the container information" % component)

        if isinstance(location, dict):
            try:
                location[value]
            except KeyError:
                raise Exception("Value '%s' not present" % value)
        elif isinstance(location, list) or isinstance(location, tuple):
            try:
                location.index(value)
            except ValueError:
                raise Exception("Value '%s' not present" % value)
        elif isinstance(location, set):
            if value not in location:
                raise Exception("Value '%s' not present" % value)
        elif str(location) != value:
            raise Exception("Value '%s' not present" % value)

@then(u'copy {src_file} to {dest_folder} in container')
def copy_file_to_container(context, src_file, dest_folder):
    container = context.containers[-1]
    container.copy_file_to_container(src_file, dest_folder)