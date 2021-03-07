"""PythonPlugin to model BIND9 daemon and views"""

import re
from xml.etree import ElementTree

from twisted.internet.defer import (
    inlineCallbacks,
    returnValue,
    )
from twisted.web.client import getPage

from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps import (
    ObjectMap,
    RelationshipMap,
    )

from ZenPacks.baileytj.BIND9.lib.utils import (
    generate_url,
    parse_xml,
    )


class BIND9(PythonPlugin):
    """BIND9 modeler plugin"""

    daemon_relname = 'bind9Daemon'
    daemon_modname = 'ZenPacks.baileytj.BIND9.BIND9DaemonURL'
    view_relname = 'bind9Views'
    view_modname = 'ZenPacks.baileytj.BIND9.BIND9ViewURL'
    view_compname = 'bind9Daemon/'

    deviceProperties = PythonPlugin.deviceProperties + (
        'zBIND9IgnoreViews',
        'zBIND9URLHostname',
        'zBIND9URLPath',
        'zBIND9URLPort',
        'zBIND9URLUseSSL',
        )

    @inlineCallbacks
    def collect(self, device, log):
        """Asynchronously collect data from device. Return a deferred."""
        log.info("%s: collecting data", device.id)

        url = generate_url(
            device.zBIND9URLHostname or device.manageIp,
            device.zBIND9URLPort,
            device.zBIND9URLPath,
            device.zBIND9URLUseSSL,
            )

        log.debug('Attempting to get xml data from {0}'.format(url))
        try:
            response = yield getPage(url)
            output = ElementTree.fromstring(response)
        except Exception as err:
            log.error('%s: %s', device.id, err)
            raise

        returnValue(output)

    def process(self, device, results, log):
        """Process results. Return iterable of datamaps or None."""

        log.info(
            'Modeler %s processing data for device %s',
            self.name(),
            device.id,
            )

        bind_data = parse_xml(results)
        ignore_view_regex = device.zBIND9IgnoreViews

        maps = list()

        om_daemon = ObjectMap(modname=self.daemon_modname)
        om_daemon.version = bind_data.get('text', 'unknown')
        # XML does not provide the host that the daemon is running on
        host = 'BIND'
        om_daemon.id = self.prepId(host)
        om_daemon.title = host + ' Daemon'

        log.debug('BIND9 Version: %s Host: %s', om_daemon.version, om_daemon.id)

        # Create the relationship map for the BIND daemon
        maps.append(RelationshipMap(
            relname=self.daemon_relname,
            modname=self.daemon_modname,
            objmaps=[om_daemon],
            ))

        # Find all the views in the results and create ObjectMaps for them
        found_views = {}
        for view in bind_data['views'].keys():

            # Skip the view if it is in the ignore regex
            if ignore_view_regex and re.match(ignore_view_regex, view):
                continue

            # Create the object map for the view and populate the properties
            view_id = self.prepId(view)
            obj = ObjectMap(
                modname=self.view_modname,
                data={'id': view_id, 'title': view},
                )

            found_views[view] = obj

        # Only add the view relationshipmap if views were found
        if len(found_views) > 0:
            maps.append(RelationshipMap(
                compname=self.view_compname + om_daemon.id,
                relname=self.view_relname,
                modname=self.view_modname,
                objmaps=found_views.values(),
                ))

        return maps
