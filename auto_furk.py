import os
import requests
from pyquery import PyQuery as pq
import argparse

ACCOUNT =  os.environ['account']
PWD = os.environ['pwd']
FURK_HOME = "https://www.furk.net"
furk_url = lambda s: FURK_HOME + s

login_payload = {
    'login': ACCOUNT,
    'pwd': PWD,
    'gigya_uid': '',
    'url': ''
}

s = requests.Session()

ARIA2_CMD = (
    "aria2c -c -i {:s}"
    " -s20 -x15 --file-allocation=none"
    " -d /dest/folders"
)

def login():
    s.headers.update({'referer': furk_url('/login')})
    login_r = s.post(furk_url('/api/login/login'), params=login_payload)
    if login_r.status_code == 200:
        print("Log in with account: {}".format(login_payload['login']))


def get_download_mirrors(df_id, link_file):
    login()
    print("Getting df ID:{}".format(df_id))

    df_r = s.get(furk_url('/df/{}'.format(df_id)))
    dom_df = pq(df_r.text)
    df_title = dom_df("h1").text()

    dom_download = dom_df("td#cell_premium_links")
    download_links = [
        elem.attrib['href'] for elem in dom_download("small a.dl_link")
    ]
    total_size = dom_df(
        "#block_info div.foldable-content ul>li:first>b"
    ).text().replace('\xa0', ' ')
    print(total_size, "||", df_title)

    download_links = [elem.attrib['href'] for elem in dom_download("small a.dl_link")]
    print("Links:\n" + "=" * 20)

    with open(link_file, 'w') as link_f:
        joint_mirrors = "\t".join(download_links)
        print(joint_mirrors)
        link_f.write(joint_mirrors + '\n')
        print("=" * 20)

    print("Combined with aria2 command:")
    print(ARIA2_CMD.format(link_file))

    print("Extracted using p7zip command:")
    print('7z x "{}.zip"'.format(df_title))

def make_argparser():
    parser =  argparse.ArgumentParser()
    parser.add_argument('df_id', metavar='DF_ID', type=str,
                        help='Furk download df id')
    parser.add_argument('link_file', nargs='?', type=str,
                        default='mirrors.link',
                        help='file to store mirror links (mirrors.link)')
    return parser


def main():
    parser = make_argparser()
    args = parser.parse_args()
    get_download_mirrors(args.df_id, args.link_file)

if __name__ == '__main__':
    main()

