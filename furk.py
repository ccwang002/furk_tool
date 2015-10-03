"""\
Furk auto downloader

Usage:
    furk.py list [--range=<n>:<n>] [--credentials=<pth>]
    furk.py batch [--range=<n>:<n>] [--zip-only [--no-mirror]]
                  [--credentials=<pth>]
    furk.py <partial_title> [--zip-only [--no-mirror]]
    furk.py convert <result_dir>
    furk.py -h | --help
    furk.py --version

Options:
    -h --help               Show this message
    -V --version            Show version
    --range=<n>:<n>         Range of selected items using
                            Python syntax of list slice
    --zip-only              Don't get the extracted file list
    --no-mirror             Don't use mirrors
    --credentials=<pth>     Path to Furk credentials
                            [default: ./.furk_credentials]
    <partial_title>         Partial item title
    <result_dir>            Root dir of the file list

"""
__version__ = '2015.02'
from collections import OrderedDict
from os.path import expanduser
from pathlib import Path
import sys

from docopt import docopt
from pyquery import PyQuery as pq
import requests

ARGUMENT_FMT = '''\
  dir={:s}
'''

furk_link = lambda sl='': 'https://www.furk.net/%s' % sl


def conn_setup(credentials_pth):
    """Initiate furk session and return it."""
    cred_pth = Path(expanduser(credentials_pth))
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
    return list(filter(None,
        [l.lstrip() for l in html_elem.text.splitlines()]
    ))


def get_zip_mirror(r_download):
    dom_a_links = pq(r_download.text)('.col-md-4 br + div + small a')
    valid_links = filter(
        lambda e: 'title' in e.attrib and e.attrib['title'].startswith('http'),
        dom_a_links
    )
    return [elem.attrib['href'] for elem in valid_links]


def get_furk_list(ses, args):
    r_finished = ses.get(furk_link('users/files/finished'))
    dom = pq(r_finished.text)
    # create item range
    txt_range = args['--range'] or ':'
    start, end = txt_range.split(':', 1)
    start = int(start) if start else None
    end = int(end) if end else None
    item_slice = slice(start, end)

    want_dfs = OrderedDict([
        (html_elem.text, html_elem.attrib['href'])
        for html_elem in dom(
            'div.list-group-item > h4.list-group-item-heading > a:first'
        )[item_slice]
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


def furk_convert(result_root_str):
    """Replace %2F with subfoler structure."""
    result_root = Path(result_root_str)
    full_file_list = result_root.iterdir()
    for pth in full_file_list:
        splitted_pths = str(pth.relative_to(result_root)).split('%2F')
        if len(splitted_pths) == 0:
            raise ValueError("Impossible path: {!s}".format(splitted_pths))
        elif len(splitted_pths) == 1:
            continue
        else:
            new_pth = result_root / Path(*splitted_pths)
            # print(pth, '->', new_pth)
            sub_dir = new_pth.parent
            if not sub_dir.exists():
                sub_dir.mkdir(parents=True)
            pth.rename(new_pth)


def main(args):
    if args['convert']:
        furk_convert(args['<result_dir>'])
        return
    ses = conn_setup(credentials_pth=args['--credentials'])
    if args['list']:
        furk_list(ses, args)    # list mode
    elif args['batch']:
        furk_batch(ses, args)   # batch mode

def console_main():
    args = docopt(__doc__, version=__version__)
    main(args)

if __name__ == '__main__':
    console_main()
