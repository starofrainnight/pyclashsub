#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Console script for pyclashsub."""

import os
import stat
import os.path
import click
import requests
import base64
import urllib.parse
import ruamel.yaml as yaml
import datetime
import shutil
import tempfile
from urllib.parse import urlparse

@click.command()
@click.option("-c", "--config-dir", required=True, help="Clash's config directory")
@click.option("-u", "--url", required=True, help="Subscribe url from your provider")
@click.option('--no-backup', is_flag=True, help="Don't backup original config before update")
def main(config_dir, url, no_backup):
    """Clash subscriber"""
    trojan_proxy_prefix = "pyclashsub-trojan-"
    trojan_proxy_name_pattern = "%s%%s" % trojan_proxy_prefix

    cfg_path = os.path.join(config_dir, "config.yaml")
    with open(cfg_path, 'r') as f:
        cfg = yaml.load(f, yaml.RoundTripLoader)

    resp = requests.get(url)
    data = base64.b64decode(resp.content).decode('utf-8')

    # Clear all auto injected trojan proxies
    proxies = cfg["proxies"]
    if proxies is None:
        proxies = list()
    proxies = list(filter(lambda it: not it['name'].startswith(trojan_proxy_prefix), proxies))
    cfg["proxies"] = proxies

    for i, line in enumerate(data.splitlines()):
        print("%s: Found proxy %s" % (i, line))

        result = urlparse(line)
        if 'trojan' != result.scheme:
            continue

        aproxy = dict()
        aproxy['type'] = 'trojan'
        aproxy['name'] = trojan_proxy_name_pattern % i
        aproxy['server'] = result.hostname
        aproxy['port'] = result.port
        aproxy['password'] = result.username

        qs = urllib.parse.parse_qs(result.query)
        qs_value = qs.get('allowInsecure', list())
        if (len(qs_value) > 0) and bool(int(qs_value[0])):
            aproxy['skip-cert-verify']= True

        qs_value = qs.get('sni', list())
        if len(qs_value) > 0:
            aproxy['sni'] = qs_value[0]

        proxies.append(aproxy)

    if not no_backup:
        # Backup original config file
        shutil.copy2(cfg_path, "%s.%s" % (cfg_path, datetime.datetime.today().isoformat()))
    cfg_mode = os.stat(cfg_path).st_mode

    # Dump to temporary file
    temp_cfg_file = tempfile.NamedTemporaryFile("w+")
    yaml.dump(cfg, temp_cfg_file, Dumper=yaml.RoundTripDumper)

    # Overwrite the cfg file by generated temporary file
    shutil.copy2(temp_cfg_file.name, cfg_path)
    # Recover the cfg file mode
    os.chmod(cfg_path, cfg_mode)


if __name__ == "__main__":
    main()
