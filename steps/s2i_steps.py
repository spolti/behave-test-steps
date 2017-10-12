from behave import then, given
import logging
import os
import tempfile

from container import Container
from steps import _execute


LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT)


def s2i_inner(context, application, path='.', env="", incremental=False, tag="master"):
    """Perform an S2I build, that may fail or succeed."""
    # set up the environment option, if supplied
    if context.table:
        envfile = tempfile.NamedTemporaryFile('wb')
        for row in context.table:
            envfile.write("%s=%s\n" % (row['variable'], row['value']))
        envfile.flush()
        env = '-E "%s"' % envfile.name

    context.image = context.config.userdata.get('IMAGE', 'ctf')

    mirror = ""

    if os.getenv("CI", False):
        mirror = "-e 'MAVEN_MIRROR_URL=http://ce-nexus.usersys.redhat.com/content/groups/public'"

    image_id = "integ-" + context.image
    command = "s2i build --loglevel=5 --force-pull=false %s --context-dir=%s -r=%s %s %s %s %s %s" % (
        mirror, path, tag, env, application, context.image, image_id, "--incremental" if incremental else ""
    )
    logging.info("Executing new S2I build...")

    output = _execute(command)
    if output:
        context.config.userdata['s2i_build_log'] = output
    return output


@given(u's2i build {application}')
@given(u's2i build {application} using {tag}')
@given(u's2i build {application} from {path}')
@given(u's2i build {application} from {path} using {tag}')
@given(u's2i build {application} from {path} with env')
@given(u's2i build {application} from {path} with env using {tag}')
@given(u's2i build {application} from {path} with env and {incremental}')
@given(u's2i build {application} from {path} with env and {incremental} using {tag}')
def s2i_build(context, application, path='.', env="", incremental=False, tag="master"):
    """Perform an S2I build, that must succeed."""
    if s2i_inner(context, application, path, env, incremental, tag):
        image_id = "integ-" + context.image
        logging.info("S2I build succeeded, image %s was built" % image_id)
        container = Container(image_id, name=context.scenario.name)
        container.start()
        context.containers.append(container)
    else:
        raise Exception("S2I build failed, check logs!")


@given(u'failing s2i build {application} from {path} using {tag}')
def failing_s2i_build(context, application, path='.', env="", incremental=False, tag="master"):
    if not s2i_inner(context, application, path, env, incremental, tag):
        logging.info("S2I build failed (as expected)")
    else:
        raise Exception("S2I build succeeded when it shouldn't have")


@then(u's2i build log should contain {phrase}')
def s2i_build_log_should_contain(context, phrase):
    if phrase in context.config.userdata['s2i_build_log']:
        return True

    raise Exception("Phrase '%s' was not found in the output of S2I" % phrase)


@then(u's2i build log should not contain {phrase}')
def s2i_build_log_should_not_contain(context, phrase):
    try:
        s2i_build_log_should_contain(context, phrase)
    except:
        return True

    raise Exception("Phrase '%s' was found in the output of S2I" % phrase)
