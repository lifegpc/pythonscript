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
ori = load(get_src(config["src"]), Loader=SafeLoader)
with open(config["dest"]) as f:
    dest = load(f, Loader=SafeLoader)
dest["proxies"] = ori["proxies"]
if "proxies" in config:
    dest["proxies"] += config["proxies"]
dest["proxy-groups"] = ori["proxy-groups"]
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
if 'rules' in config:
    dest['rules'] = config['rules']
with open(config["dest"], "w") as f:
    dump(dest, f, Dumper=SafeDumper, allow_unicode=True)
