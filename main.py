#!/usr/bin/env python3

from gevent import monkey; monkey.patch_all()
import sys
import time
import gevent
import json
import requests
import ipaddress
import argparse

from functools import partial
from gevent import socket
from gevent.pool import Pool

gevent.config.resolver = 'ares'

URL = 'https://raw.githubusercontent.com/zapret-info/z-i/master/dump.csv'


def parse_headers(headers):
    size = int(headers.get('Content-Length', '0'))
    etag = headers.get('ETag', '""').strip('"')
    return size, etag


class State:
    STATE = 'state.json'

    def load(self):
        size, etag = None, None
        try:
            with open(self.STATE) as f:
                state = json.load(f)
                size = state.get('size')
                etag = state.get('etag')
        except Exception as ex:
            pass
        return size, etag

    def save(self, size, etag):
        try:
            with open(self.STATE, 'w') as f:
                json.dump({'size': size, 'etag': etag}, f)
        except Exception as ex:
            print(ex)
            pass


def ip_parse(data):
    return set(data.replace(' ', '').split('|'))


def summarize(*args, **kwargs):
    target = kwargs.get('target', 16)
    ip_set, net_set = set(), set()

    for arg in args:
        ip_set.update(arg)

    for ip in ip_set:
        if ip:
            net = ipaddress.IPv4Network(ip, strict=False)
            if net.prefixlen > target:
                net = net.supernet(new_prefix=target)
            net_set.add(net)
    return ipaddress.collapse_addresses(net_set)


def fetch(read_state=True, write_state=True):
    ips, domains = set(), set()

    s = requests.Session()

    if read_state:
        state = State()
        psize, petag = state.load()
        with s.head(URL) as h:
            size, etag = parse_headers(h.headers)
            if size == psize and etag == petag:
                sys.exit(0)

    with s.get(URL, stream=True) as r:
        if r.status_code == 200:
            for line in r.iter_lines():
                d = line.decode('cp1251')
                if d.startswith('Updated:'):
                    continue
                item = d.split(';')
                domain = item[1]
                if domain.startswith('*'):
                    domain = domain.lstrip('*.')
                domains.add(domain)
                ips.update(ip_parse(item[0]))
            if write_state:
                state.save(size, etag)
    return ips, domains


def resolve_fn(d, timeout=4):
    ips = None
    try:
        with gevent.Timeout(timeout, False):
            ips = {f[4][0] for f in socket.getaddrinfo(d, 80, socket.AF_INET, 0, socket.IPPROTO_TCP)}
    except socket.gaierror as ex:
        pass
    return d, ips


def resolve(domains, intensity=100, timeout=2, dump=False):
    ips = set()
    res = dict()
    pool = Pool(intensity)
    fn = partial(resolve_fn, timeout=timeout)
    for domain, ip in pool.imap_unordered(fn, domains):
        if ip:
            res[domain] = tuple(ip)
            ips.update(ip)

    if dump:
        filename = time.strftime('%Y%m%d_%H%M%S.resolved.json')
        with open(filename, 'w') as f:
            json.dump(res, f)
    return ips


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Roscomnadzor blacklist aggreation tool.", allow_abbrev=False)

    parser.add_argument(
        '--target', metavar='', type=int, default=24, help="Prefix aggregation target mask length"
        )

    parser.add_argument(
        '--write', dest='write', metavar='', type=int, default=False, help="Write state file to disk(0 or 1)"
        )
    parser.add_argument(
        '--read', dest='read', metavar='', type=int, default=False, help="Read state file from disk(0 or 1)"
        )
    parser.add_argument(
        '--qps', dest='intensity', metavar='QPS', type=int, default=200, help="The number of simultaneous DNS requests"
        )

    parser.add_argument(
        '--dump', dest='dump', metavar='', type=int, default=True, help="Write resolv dump to disk(0 or 1)"
        )

    parser.add_argument(
        '--outfile', dest='outfile', metavar='', type=str, default=None, help="Write output prefix list to disk(0 or 1)"
        )

    args = parser.parse_args()
    i, d = fetch(read_state=args.read, write_state=args.write)
    r = tuple(resolve(d, intensity=args.intensity, dump=args.dump))
    s = sorted(tuple(summarize(i, r, target=args.target)))

    if args.outfile:
        try:
            with open(args.outfile, 'w') as f:
                for net in s:
                    print(net, file=f)
        except Exception:
            pass

    else:
        for c, net in enumerate(s):
            print(net, file=sys.stdout)
