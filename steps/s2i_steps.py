from behave import then, given
import logging
import re
import os
import tempfile

from container import Container
from steps import _execute


LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT)


def s2i_inner(context, application, path='.', env="", incremental=False, tag="master", runtime_image=""):
    """Perform an S2I build, that may fail or succeed."""
    # set up the environment option, if supplied
    if context.table:
        envfile = tempfile.NamedTemporaryFile('w')
        for row in context.table:
            envfile.write("%s=%s\n" % (row.get('variable'), row.get('value')))
        envfile.flush()
        env = '-E "%s"' % envfile.name

    context.image = context.config.userdata.get('IMAGE', 'ctf')

    mirror = ""

    if os.getenv("CI", False):
        mirror = "-e 'MAVEN_MIRROR_URL=http://nexus-ce.cloud.paas.upshift.redhat.com/repository/maven-public/'"

    if os.getenv("MAVEN_MIRROR_URL", False):
        mirror = "-e 'MAVEN_MIRROR_URL=%s'" % os.getenv("MAVEN_MIRROR_URL")
        
    image_id = "integ-" + context.image
    command = "s2i build --loglevel=5 --pull-policy if-not-present %s --context-dir=%s -r=%s %s %s %s %s %s %s" % (
        mirror, path, tag, env, application, context.image, image_id, "--incremental" if incremental else "",
        "--runtime-image="+runtime_image if runtime_image else ""
    )
    logging.info("Executing new S2I build with the command [%s]..." % command)

    output = _execute(command)
    if output:
        context.config.userdata['s2i_build_log'] = output
    return output

@given(u's2i build {application} from {path} with env and {incremental} using {tag} without running')
def s2i_build_no_run(context, application, path='.', env="", incremental=False, tag="master"):
    s2i_build(context, application, path, env, incremental, tag, False, "")

@given(u's2i build {application}')
@given(u's2i build {application} using {tag}')
@given(u's2i build {application} from {path}')
@given(u's2i build {application} from {path} using {tag}')
@given(u's2i build {application} from {path} with env')
@given(u's2i build {application} from {path} with env using {tag}')
@given(u's2i build {application} from {path} with env and {incremental}')
@given(u's2i build {application} from {path} with env and {incremental} using {tag}')
@given(u's2i build {application} from {path} using {tag} and runtime-image {runtime_image}')
def s2i_build(context, application, path='.', env="", incremental=False, tag="master", run=True, runtime_image=""):
    """Perform an S2I build, that must succeed."""
    if s2i_inner(context, application, path, env, incremental, tag, runtime_image):
        image_id = "integ-" + context.image
        logging.info("S2I build succeeded, image %s was built" % image_id)
        if run:
            container = Container(image_id, name=context.scenario.name)
            container.start()
            context.containers.append(container)
    else:
        raise Exception("S2I build failed, check logs!")

@given(u'failing s2i build {application} from {path} using {tag}')
def failing_s2i_build(context, application, path='.', env="", incremental=False, tag="master", runtime_image=""):
    if not s2i_inner(context, application, path, env, incremental, tag, runtime_image):
        logging.info("S2I build failed (as expected)")
    else:
        raise Exception("S2I build succeeded when it shouldn't have")


@then(u's2i build log should contain {phrase}')
def s2i_build_log_should_contain(context, phrase):
    if phrase in context.config.userdata['s2i_build_log']:
        return True

    raise Exception("Phrase '%s' was not found in the output of S2I" % phrase)

@then(u's2i build log should match regex {regex}')
def s2i_build_log_should_match_regex(context, regex):
    if re.search(regex, context.config.userdata['s2i_build_log'], re.MULTILINE):
        return True

    raise Exception("Regex '%s' did not match in the output of S2I" % regex)

@then(u's2i build log should not contain {phrase}')
def s2i_build_log_should_not_contain(context, phrase):
    try:
        s2i_build_log_should_contain(context, phrase)
    except:
        return True

    raise Exception("Phrase '%s' was found in the output of S2I" % phrase)
