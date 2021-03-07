"""DSPlugin to monitor performance of BIND9URLDaemons"""

import logging

from xml.etree import ElementTree

from twisted.internet.defer import (
    inlineCallbacks,
    returnValue,
    )
from twisted.web.client import getPage

from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSourcePlugin,
    )

from ZenPacks.baileytj.BIND9.lib.utils import (
    generate_url,
    parse_xml,
    )

LOG = logging.getLogger('zen.BIND9URL')


class URL(PythonDataSourcePlugin):
    """BIND9 URL data source plugin"""

    proxy_attributes = (
        'zBIND9URLHostname',
        'zBIND9URLPath',
        'zBIND9URLPort',
        'zBIND9URLUseSSL',
        )

    @classmethod
    def config_key(cls, datasource, context):
        """Return list used to split configurations at the collector."""

        return (
            context.device().id,
            datasource.getCycleTime(context),
            datasource.plugin_classname,
            )

    @classmethod
    def params(cls, datasource, context):
        """Return params dictionary needed for this plugin."""

        return {
            'title' : context.title,
            }

    @inlineCallbacks
    def collect(self, config):
        """Collect the data needed for this plugin."""

        # URL should be the same for all datasources
        ds0 = config.datasources[0]
        url = generate_url(
            ds0.zBIND9URLHostname or config.id,
            ds0.zBIND9URLPort,
            ds0.zBIND9URLPath,
            ds0.zBIND9URLUseSSL,
            )

        LOG.debug('Attempting to get xml data from %s', url)
        try:
            response = yield getPage(url)
            output = ElementTree.fromstring(response)
        except Exception:
            LOG.exception('failed to get xml from %s', url)
            raise

        returnValue(output)

    def onSuccess(self, result, config):
        """Called only on success of collect."""

        data = self.new_data()
        bind_data = parse_xml(result)

        # datasources should contain the daemon component and all the view
        # components
        for datasource in config.datasources:
            # datasource is a daemon
            if datasource.component == 'BIND':
                values = bind_data['server']
            # datasource is a view
            else:
                view = datasource.params['title']
                values = bind_data['views'][view]

            for point in datasource.points:
                if point.id in values:
                    dpname = datasource.datasource + '_' + point.id
                    data['values'][datasource.component][dpname] = \
                        (values[point.id], 'N')

        LOG.debug('parsed xml data: %s', data.items())

        return data

    def onError(self, result, config):
        """Called only on error of collect or onSuccess."""

        LOG.critical('%s: %s', config.id, result.getErrorMessage())
        LOG.debug(str(result))

        return self.new_data()
