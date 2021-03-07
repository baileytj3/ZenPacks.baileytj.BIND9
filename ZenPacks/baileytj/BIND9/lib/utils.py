"""Utility functions for the ZenPack"""

import re

from collections import defaultdict

def generate_url(hostname, port, path, ssl):
    """Generate the URL for accessing the BIND XML Statistics."""

    protocol = 'https' if ssl else 'http'
    path = path.lstrip('/')
    url = '{0}://{1}:{2}/{3}'.format(
        protocol,
        hostname,
        str(port),
        path,
        )

    return url

def parse_section_view(pattern, view, string, prefix):
    """Parse a section of rndc output containing a view.

    Given a regex pattern and string to match against, this function will
    return a dict of the values within the section of rndc output nested within
    a dict where the keys are the view names that were matched.
    """

    view_regex = r'\[View: (?P<view>\S+?)[ \]](?:\(Cache:\s+\S+?\)])?\s' \
                 r'(?P<values>[\s\S]*?)(?=$|\[)'
    ret = dict()

    section = re_search_group(pattern, string)

    if section:
        # Find the requested view and process the values
        for match in re.finditer(view_regex, section):
            if match.groupdict()['view'] == view:
                values = match.groupdict()['values']
                ret = parse_values(values, prefix)

    return ret

def parse_section(pattern, string, prefix):
    """Parse a section of rndc output.

    Given a regex pattern and string to match against, this function will
    return a dict of the values within the section of rndc output matched by
    the pattern.
    """

    values = re_search_group(pattern, string)
    return parse_values(values, prefix)

def parse_values(string, prefix):
    """Parse the value name pairs output by rndc.

    Parse the lines output by rndc with a value and name that are separated by
    a space character. Spaces are removed from the, it is converted to lower
    case, and prefixed with the prefix variable before becoming the key to the
    dict that is returned. The value gets converted to an integer and is the
    value in the dict for the key.

    The string passed to the function can contain multiple lines separated by
    the '\n' character. A dict of all of the parsed key/value pairs is
    returned.
    """

    ret = dict()
    for match in string.splitlines():
        val, name = match.strip().split(' ', 1)
        idx = prefix + name.replace(' ', '').lower()
        ret[idx] = int(val)

    return ret

def parse_xml(xmltree):
    """Recursively parse the BIND XML output into a dict.

    When an element with a tag of 'counters' is encountered, the 'type'
    associated with that element becomes the prefix for the names of all the
    child 'counter' objects.

    Eg.

        <counters type="qtype">
          <counter name="A">10</counter>
        </counters>

    becomes

        { 'qtype-a': 10 }

    When an element with a tag of 'view' is encountered, the 'name' associated
    with that element becomes the key for the dict.

    Eg.

        <view name='_default'>
          <counters type="qtype">
            <counter name="A">10</counter>
          </counters>
        </view>

    becomes

        { '_default': { 'qtype-a': 10 }}

    When an element with a tag of 'cache' is encounters, the 'name' associated
    with that element becomes the key for the dict. The nested rrset elements
    contain children elements with tags of name and counter that become the key
    and value. The key is prefixed with 'cache-'.

    Eg.

        <cache name="_default">
          <rrset>
            <name>A</name>
            <counter>10</counter>
          </rrset>
        </cache>

    becomes

        { '_default': { 'cache-a': 10 }}

    When there are more than 1 elements at a given depth that are not tags of
    'counters' nor 'cache', the parse_xml function is called recursively to
    parse each one.
    """

    res = defaultdict(dict)

    for element in xmltree:

        if element.tag == 'counters':
            for counter in element:
                key = '-'.join([element.get('type'), counter.get('name')])
                key = key.lower()
                res[key] = int(counter.text)

        elif element.tag == 'cache':
            for rrset in element:
                name = rrset.find('./name').text.lower()
                count = rrset.find('./counter').text
                key = '-'.join(['cache', name])
                res[key] = int(count)

        elif len(element) > 1:
            key = element.tag
            if element.tag == 'view':
                key = element.get('name')

            res[key] = parse_xml(element)

        else:
            key = element.tag
            res[key] = element.text

    return res

def re_search_group(pattern, string, flags=0, group=0, default=''):
    """Search the string for the given patter and return the group.

    Perform a regex search on the given string with the given pattern. If there
    is a match the requested group will be returned. If the group is unable to
    be returned default will be returned instead. Note that the pattern must
    have a capturing group defined for the group to be returned.
    """
    match = re.search(pattern, string, flags)
    ret = default
    if match:
        try:
            ret = match.groups()[group]
        except IndexError:
            pass

    return ret
