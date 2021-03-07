""" CommandPlugin to model BIND9 daemon and views"""

import re

from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin
from Products.DataCollector.plugins.DataMaps import (
    ObjectMap,
    RelationshipMap,
    )

from ZenPacks.baileytj.BIND9.lib.utils import re_search_group


class BIND9(CommandPlugin):
    """BIND9 modeler plugin"""

    daemon_relname = 'bind9Daemon'
    daemon_modname = 'ZenPacks.baileytj.BIND9.BIND9DaemonRNDC'
    view_relname = 'bind9Views'
    view_modname = 'ZenPacks.baileytj.BIND9.BIND9ViewRNDC'
    view_compname = 'bind9Daemon/'

    deviceProperties = CommandPlugin.deviceProperties + (
        'zBIND9IgnoreViews',
        'zBIND9RNDCBinaryPath',
        'zBIND9RNDCExecPrefix',
        'zBIND9RNDCStatsPath',
        )

    command = (
        # If the command does not start with a path, Zenoss will add
        # $ZENHOME/libexec as a prefic to the command. If zBIND9ExecPrefix is
        # empty Zenoss would add the prefix. The echo prevents this "feature".
        '/bin/echo > /dev/null;'
        '${here/zBIND9RNDCExecPrefix} ${here/zBIND9RNDCBinaryPath} status;'
        '${here/zBIND9RNDCExecPrefix} ${here/zBIND9RNDCBinaryPath} stats;'
        'tac ${here/zBIND9RNDCStatsPath} |'
        ' awk \'!f; /\\+\\+\\+/{f=1};\' | tac;'
        )

    def process(self, device, results, log):
        """Process the data this plugin collects."""
        log.info(
            'Modeler %s processing data for device %s',
            self.name(),
            device.id,
            )

        # Regex's used in processing the command results
        host_regex = r'^running on (\S+):'
        version_regex = r'^version:\s+(\S+\s+\S+)'
        view_regex = r'^\[View:\s(\S+?)]'
        ignore_view_regex = getattr(device, 'zBIND9IgnoreViews', '')

        maps = list()

        # Create object map for the BIND daemon and populate the properties
        om_daemon = ObjectMap(modname=self.daemon_modname)
        om_daemon.version = re_search_group(
            version_regex,
            results,
            flags=re.MULTILINE,
            default='unknown',
            )

        host = re_search_group(
            host_regex,
            results,
            flags=re.MULTILINE,
            default='BIND',
            )
        om_daemon.id = self.prepId(host)
        om_daemon.title = host + ' Daemon'

        log.debug(
            'BIND9 Version: %s Host: %s',
            om_daemon.version,
            om_daemon.id,
            )

        # Create the relationship map for the BIND daemon
        maps.append(RelationshipMap(
            relname=self.daemon_relname,
            modname=self.daemon_modname,
            objmaps=[om_daemon],
            ))

        # Find all the views in the results and create ObjectMaps for them
        found_views = {}
        for match in re.finditer(view_regex, results, re.MULTILINE):
            view = match.groups()[0]

            # Skip the view if it is in the ignore regex
            if ignore_view_regex and re.match(ignore_view_regex, view):
                continue

            # Skip the view if it has already been found
            if view in found_views:
                continue

            # Create the object map for the view and populate the properties
            view_id = self.prepId(view)
            obj = ObjectMap(
                modname=self.view_modname,
                data={'id': view_id, 'title': view},
                )

            found_views[view] = obj

        # Only add the view relationship map if views were found
        # There is a 'default' view BIND creates, but a permission issue
        # could prevent parsing the views from the stats output.
        if len(found_views) > 0:
            maps.append(RelationshipMap(
                compname=self.view_compname + om_daemon.id,
                relname=self.view_relname,
                modname=self.view_modname,
                objmaps=found_views.values(),
                ))

        return maps
