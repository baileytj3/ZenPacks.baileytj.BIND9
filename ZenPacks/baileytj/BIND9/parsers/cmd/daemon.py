"""CommandParser to parse performance output from BIND9Daemons"""

from itertools import chain

from Products.ZenRRD.CommandParser import CommandParser

from ZenPacks.baileytj.BIND9.lib.utils import parse_section


class daemon(CommandParser):

    def processResults(self, cmd, result):
        query_regex = r'Incoming Queries \+\+\s((?!\+)[\s\S]*?)\s\+'
        rcode_regex = r'Outgoing Rcodes \+\+\s((?!\+)[\s\S]*?)\s\+'
        total_regex = r'Incoming Requests \+\+\s((?!\+)[\s\S]*?)\s\+'

        # Parse the values from the required sections of output
        query = parse_section(query_regex, cmd.result.output, 'qtype-')
        rcode = parse_section(rcode_regex, cmd.result.output, 'rcode-')
        total = parse_section(total_regex, cmd.result.output, 'opcode-')

        # Merge the values into a single dictionary
        values = dict(chain(query.items(), rcode.items(), total.items()))

        # Add the values to the result
        for point in cmd.points:
            if point.id in values:
                result.values.append((point, values[point.id]))
