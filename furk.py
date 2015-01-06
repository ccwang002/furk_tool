"""\
Furk auto downloader

Usage:
    furk.py list [--top=<num>]
    furk.py batch [--top=<num>] [--zip-only [--no-mirror]]
    furk.py <partial_title> [--zip-only [--no-mirror]]
    furk.py -h | --help
    furk.py --version

Options:
    -h --help               Show this message
    -V --version            Show version
    -t <num> --top=<num>    Only get top <num> items
    --zip-only              Don't get the extracted file list
    --no-mirror             Don't use mirrors
    <partial_title>         Partial item title

"""
__version__ = '2015.01'
from collections import OrderedDict
from pathlib import Path
import sys

from docopt import docopt
from pyquery import PyQuery as pq
import requests

ARGUMENT_FMT = '''\
  dir={:s}
'''

furk_link = lambda sl='': 'https://www.furk.net/%s' % sl


def conn_setup():
    """Initiate furk session and return it."""
    cred_pth = Path('.furk_credentials')
    if not cred_pth.exists():
        print("put account and password info at ./.furk_credentials")
        sys.exit(1)
    with cred_pth.open('r') as f:
        ACC = next(f).strip().split(' = ')[-1]
        PWD = next(f).strip().split(' = ')[-1]

    ses = requests.Session()
    r = ses.get(furk_link())
    login_payload = {
        'login': ACC,
        'pwd': PWD,
        'gigya_uid': '',
        'url': ''
    }
    ses.headers.update({'referer': furk_link('login')})
    r = ses.post(furk_link('api/login/login'), params=login_payload)
    if not r.ok:
        sys.exit('Cannot setup connection with furk.')
    return ses


def get_uri_list(r_download):
    html_elem = pq(r_download.text)("textarea#plain_list")[0]
    if html_elem is None:
        raise ValueError("Parsing Error")
    return html_elem.text.splitlines()


def get_zip_mirror(r_download):
    dom_download = pq(r_download.text)("td#cell_premium_links")
    return [
        elem.attrib['href']
        for elem in dom_download("small a.dl_link")
    ]


def get_furk_list(ses, args):
    r_finished = ses.get(furk_link('users/files/finished'))
    dom = pq(r_finished.text)
    if args['--top'] is not None:
        top_num = int(args['--top'])
    else:
        top_num = args['--top']
    item_sl = slice(None, top_num)
    want_dfs = OrderedDict([
        (html_elem.text, html_elem.attrib['href'])
        for html_elem in dom('div.tor-box h2 a:first')[item_sl]
    ])
    return want_dfs


def get_furk_batch(ses, args):
    """Batch download items."""
    want_dfs = get_furk_list(ses, args)
    full_down_links = OrderedDict()
    for df_title, df_sublink in want_dfs.items():
        r_down = ses.get(furk_link(df_sublink))
        if args['--zip-only']:
            full_down_links[df_title] = get_zip_mirror(r_down)
        else:
            full_down_links[df_title] = get_uri_list(r_down)
    return full_down_links


def furk_list(ses, args):
    """List finished item list."""
    want_dfs = get_furk_list(ses, args)
    for df_title, df_sublink in want_dfs.items():
        print(df_sublink, df_title)


def furk_batch(ses, args):
    full_down_links = get_furk_batch(ses, args)
    for df_title, df_links in full_down_links.items():
        if args['--zip-only']:
            if args['--no-mirror']:
                print(df_links[0])
            else:
                print('\t'.join(df_links))
        else:
            # create aria2 uri
            if len(df_links) == 1:
                print(df_links[0])
            else:
                arg = ARGUMENT_FMT.format(df_title)
                for link in df_links:
                    print(link)
                    print(arg)


def main(args):
    ses = conn_setup()
    if args['list']:
        furk_list(ses, args)    # list mode
    elif args['batch']:
        furk_batch(ses, args)   # batch mode


if __name__ == '__main__':
    args = docopt(__doc__, version=__version__)
    # print(args)
    main(args)
