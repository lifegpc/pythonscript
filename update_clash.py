from yaml import load, dump
try:
    from yaml import CSafeLoader as SafeLoader, CSafeDumper as SafeDumper
except ImportError:
    from yaml import SafeLoader, SafeDumper
from argparse import ArgumentParser
import requests
import re


def get_src(src):
    if isinstance(src, str):
        return requests.get(src).content
    else:
        url = src["url"]
        headers = {}
        if "headers" in src:
            headers = src["headers"]
        return requests.get(url, headers=headers).content


p = ArgumentParser()
p.add_argument("-c", "--config", help="configurtion files",
               default="update_clash.yaml")
arg = p.parse_intermixed_args()
with open(arg.config) as f:
    config = load(f, Loader=SafeLoader)
src = config["src"]
if not isinstance(src, list):
    src = [src]
with open(config["dest"]) as f:
    dest = load(f, Loader=SafeLoader)
dest["proxies"] = []
dest["proxy-groups"] = []
more_groups = []
for s in src:
    add_group = False
    if isinstance(s, dict):
        if "add-group" in s and s["add-group"] and "name" in s and s["name"]:
            add_group = True
    ori = load(get_src(s), Loader=SafeLoader)
    dest["proxies"] += ori["proxies"]
    dest["proxy-groups"] += ori["proxy-groups"]
    if add_group:
        more_groups.append({
            "name": s["name"],
            "type": "select",
            "proxies": [i["name"] for i in ori["proxies"]]
        })
if "proxies" in config:
    dest["proxies"] += config["proxies"]
if "proxy-groups" in config:
    dest["proxy-groups"] = []
    for group in config["proxy-groups"]:
        if 'proxies' not in group:
            group['proxies'] = []
        if 'match-all' in group:
            if group['match-all']:
                for i in dest["proxies"]:
                    group['proxies'].append(i['name'])
            del group['match-all']
        if 'match' in group:
            for m in group['match']:
                for i in dest["proxies"]:
                    if re.match(m, i['name']):
                        if i['name'] not in group['proxies']:
                            group['proxies'].append(i['name'])
            del group['match']
        if 'add-direct' in group:
            if group['add-direct']:
                group['proxies'].append('DIRECT')
            del group['add-direct']
        dest["proxy-groups"].append(group)
dest["proxy-groups"] += more_groups
if 'rules' in config:
    dest['rules'] = config['rules']
with open(config["dest"], "w") as f:
    dump(dest, f, Dumper=SafeDumper, allow_unicode=True)
