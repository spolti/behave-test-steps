from behave import then, given
from lxml import etree
import time
from steps import TIMEOUT


@given('XML namespace {prefix}:{url}')
def register_xml_namespace(context, prefix, url):
    if not hasattr(context, 'xml_namespaces'):
        context.xml_namespaces = {}
    context.xml_namespaces[prefix] = url


@given('XML namespaces')
def register_xml_namespaces(context):
    context.xml_namespaces = {}
    for row in context.table:
        context.xml_namespaces[row['prefix']] = row['url']


@then('XML file {xml_file} should contain value {value} on XPath {xpath}')
def check_xpath(context, xml_file, xpath, value):
    start_time = time.time()

    container = context.containers[-1]

    while time.time() < start_time + TIMEOUT:
        content = container.execute(cmd="cat %s" % xml_file)
        document = etree.fromstring(content)

        if 'xml_namespaces' in context:
            result = document.xpath(xpath, namespaces=context.xml_namespaces)
        else:
            result = document.xpath(xpath)

        if isinstance(result, list):
            for option in result:
                if isinstance(option, str):
                    if str(option) == str(value):
                        return True
                else:
                    # We assume here that result is Element class
                    if option.text == str(value):
                        return True
        else:
            if result == safe_cast_int(result):
                return True

        time.sleep(1)

    raise Exception('XPath expression "%s" did not match "%s"' % (xpath, value), content)


@then('XML file {xml_file} should have {count} elements on XPath {xpath}')
def check_xml_element_count(context, xml_file, xpath, count):
    check_xpath(context, xml_file, 'count(' + xpath + ')', count)


def safe_cast_int(value, default=None):
    try:
        return int(value)
    except ValueError:
        return default
