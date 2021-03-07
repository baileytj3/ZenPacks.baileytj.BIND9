# ZenPacks.baileytj.BIND9

[![GitHub Release](https://img.shields.io/github/v/release/baileytj3/ZenPacks.baileytj.BIND9?include_prereleases)](https://github.com/baileytj3/ZenPacks.baileytj.BIND9/releases/latest)

ZenPack to monitor a BIND9 daemon

## Requirements
* [PythonCollector](https://help.zenoss.com/in/zenpack-catalog/open-source/pythoncollector) ZenPack
* [ZenPackLib](https://help.zenoss.com/in/zenpack-catalog/open-source/zenpacklib)

## zProperties
* `zBIND9IgnoreViews`
  * Regex of BIND views to ignore
  * Default: \_bind
* `zBIND9RNDCBinaryPath` - **required when using cmd datasource**
  * Path to the 'rndc' executable
  * Default: /usr/sbin/rndc
* `zBIND9RNDCExecPrefix`
  * Command to run prior to 'rndc'
  * Default: /usr/bin/sudo
* `zBIND9RNDCStatsPath` - **required when using cmd datasource**
  * Path to the stats file produced by 'rndc stats'
  * Default: /var/cache/bind/named.stats
* `zBIND9URLHostname`
  * Override the device id for accessing the BIND stats URL
  * Default:
* `zBIND9URLPath`
  * Path to use to access the BIND stats URL
  * Default: /xml/v3/server
* `zBIND9URLPort`
  * Port to use to access the BIND stats URL
  * Default: 80
* `zBIND9URLUseSSL`
  * Use https if True, http otherwise.
  * Default: False

## Usage

This ZenPack comes with two different ways to monitor BIND9. The first is by
using `rndc` via zencommand. The second is by using BIND's statistics-channel
via pythoncollector.

### RNDC

To monitor BIND9 using `rndc` the SSH user specified in `zCommandUsername` is
required to have permissions to execute the `rndc` executable and read the
statistics file that is written by the `rndc stats` command. There are two ways
to grant the required permissions.

The preferred way to grant the Zenoss SSH user the required permissions is to
add an entry in `/etc/sudoers` to allow the user to execute the required
commands via `sudo`.

Example `/etc/sudoers` addition:
```
Cmnd_Alias STATS = /usr/sbin/rndc stats
Cmnd_Alias STATUS = /usr/sbin/rndc status
zenoss  ALL=(ALL) NOPASSWD: STATS, STATUS
```

The second way to grant the Zenoss SSH user the required permissions is to add
the user to the BIND9 user group. Depending on the flavor of OS the BIND9 user
group will vary. Use this method with caution as the Zenoss SSH user will have
administrative priveleges over the BIND9 configuration.

To monitor BIND9 via the `rndc` command, bind the `baileytj.cmd.BIND9` modeler
to the device or device class.

### Statistics Channel

BIND9 also supports XML monitoring via the statistics-channel. Zenoss only
needs to be able to query the URL for BIND9 once the statistics-channel is
configured.

To monitor BIND9 via the statistics-channel, bind the `baileytj.python.BIND9`
modeler to the device or device class.

## Special Thanks
* [JRansomed](https://github.com/JRansomed) - ZenPack tester
* [daviswr](https://github.com/daviswr) - ZenPack tester
