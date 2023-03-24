#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Console script for pyclashsub."""

import os
import stat
import os.path
from typing import Any, Dict
import click
import requests
import base64
import urllib.parse
import ruamel.yaml as yaml
import datetime
import shutil
import tempfile
import demjson3
from urllib.parse import urlparse, unquote


def add_proxies_to_auto_group(cfg, proxies):
    proxy_groups = cfg["proxy-groups"]
    for agroup in proxy_groups:
        if agroup["name"] != "auto":
            continue

        agroup["proxies"] = []
        for proxy in proxies:
            agroup["proxies"].append(proxy["name"])

        break


def filter_selections(tag, includes, excludes):
    found = False
    for it in includes:
        if it in tag:
            found = True
            break

    if (not found) and (len(includes) > 0):
        return False

    for it in excludes:
        if it in tag:
            return False

    return True


@click.command()
@click.option(
    "-c", "--config-dir", required=True, help="Clash's config directory"
)
@click.option(
    "-u", "--url", required=True, help="Subscribe url from your provider"
)
@click.option(
    "--no-backup",
    is_flag=True,
    help="Don't backup original config before update",
)
def main(config_dir, url, no_backup):
    """Clash subscriber"""
    proxy_prefix = "pyclashsub-proxy-"
    proxy_name_pattern = "%s%%s" % proxy_prefix

    cfg_path = os.path.join(config_dir, "config.yaml")
    with open(cfg_path, "r") as f:
        cfg: Dict[Any] = yaml.load(f, yaml.RoundTripLoader)

    resp = requests.get(url)
    data = base64.b64decode(resp.content).decode("utf-8")

    # Clear all auto injected trojan proxies
    proxies = cfg["proxies"]
    if proxies is None:
        proxies = list()
    proxies = list(
        filter(lambda it: not it["name"].startswith(proxy_prefix), proxies)
    )
    cfg["proxies"] = proxies

    includes = cfg.get("pyclashsub", {}).get("includes", [])
    excludes = cfg.get("pyclashsub", {}).get("excludes", [])

    i = -1
    for proxy_idx, line in enumerate(data.splitlines()):
        print("%s: Found proxy %s" % (proxy_idx, line))

        result = urlparse(line)

        if "trojan" == result.scheme:
            node_text = unquote(result.fragment).strip()

            print("Proxy tag: %s" % node_text)
            if not filter_selections(node_text, includes, excludes):
                print("Skipped")
                continue

            aproxy = dict()
            aproxy["type"] = "trojan"
            aproxy["name"] = proxy_name_pattern % i
            aproxy["server"] = result.hostname
            aproxy["port"] = result.port
            aproxy["password"] = result.username

            qs = urllib.parse.parse_qs(result.query)
            qs_value = qs.get("allowInsecure", list())
            if (len(qs_value) > 0) and bool(int(qs_value[0])):
                aproxy["skip-cert-verify"] = True

            qs_value = qs.get("sni", list())
            if len(qs_value) > 0:
                aproxy["sni"] = qs_value[0]

            proxies.append(aproxy)
        elif "vmess" == result.scheme:
            data = demjson3.decode(base64.b64decode(result.netloc))

            node_text = data["ps"]
            print("Proxy tag: %s" % node_text)
            if not filter_selections(node_text, includes, excludes):
                print("Skipped")
                continue

            aproxy = dict()
            aproxy["type"] = "vmess"
            aproxy["name"] = proxy_name_pattern % i
            aproxy["cipher"] = "auto"
            aproxy["server"] = data["add"]
            aproxy["port"] = int(data["port"])
            aproxy["uuid"] = data["id"]
            aproxy["alterId"] = int(data["aid"])
            aproxy["skip-cert-verify"] = True
            if "udp" == data.get("net"):
                aproxy["udp"] = True

            if "tls" == data.get("tls"):
                aproxy["tls"] = True

            if data.get("sni"):
                aproxy["sni"] = data["sni"]
            proxies.append(aproxy)
        else:
            continue

        i += 1

    add_proxies_to_auto_group(cfg, proxies)

    if not no_backup:
        # Backup original config file
        shutil.copy2(
            cfg_path,
            "%s.%s" % (cfg_path, datetime.datetime.today().isoformat()),
        )
    cfg_mode = os.stat(cfg_path).st_mode

    # Dump to temporary file
    temp_cfg_file = tempfile.NamedTemporaryFile("w+")
    yaml.dump(
        cfg,
        temp_cfg_file,
        Dumper=yaml.RoundTripDumper,
        encoding="utf-8",
        allow_unicode=True,
    )

    # Overwrite the cfg file by generated temporary file
    shutil.copy2(temp_cfg_file.name, cfg_path)
    # Recover the cfg file mode
    os.chmod(cfg_path, cfg_mode)


if __name__ == "__main__":
    main()
