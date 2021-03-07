"""CommandParser to parse performance output from BIND9Views"""

from itertools import chain

from Products.ZenRRD.CommandParser import CommandParser

from ZenPacks.baileytj.BIND9.lib.utils import parse_section_view


class view(CommandParser):

    def processResults(self, cmd, result):
        cache_regex = r'Cache Statistics \+\+\s((?!\+)[\s\S]*?)\s\+'
        query_regex = r'Outgoing Queries \+\+\s((?!\+)[\s\S]*?)\s\+'

        # Parse the values from the required section view of output
        _view = cmd.component
        cmd_result = cmd.result.output

        cache = parse_section_view(cache_regex, _view, cmd_result, 'cachestats-')
        query = parse_section_view(query_regex, _view, cmd_result, 'resqtype-')

        # Merge the values into a single dictionary
        values = dict(chain(cache.items(), query.items()))

        # Add the values to the result
        for point in cmd.points:
            if point.id in values:
                result.values.append((point, values[point.id]))
