import json
import yaml
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
else:
    from configparser import SafeConfigParser

def parse_hostfile(host):
    keys = ['host', 'username', 'password']
    values = host.split(":")
    hosts = dict(zip(keys, values))
    hosts['password'] = Password(hosts['password'])
    return hosts


def normalize_hosts(hosts):
    if hosts is None:
        return []
    if isinstance(hosts, str):
        hosts = filter(lambda h: (not h.startswith("#") and h != ""), hosts.splitlines())
        hosts = [host.strip() for host in hosts]
    return [_parse_hostfile(host) if ':' in host else {'host': host} for host in hosts]


def load_json(path):
    data = open(path, 'r').read()
    data = json.loads(data)
    




def load_yaml(path):
    pass


def load_ini(path):
    ini_config = SafeConfigParser(allow_no_value=True)
    ini_config.read(path)
    options.hosts = [server[1] for server in ini_config.items(path)]
    if ini_config.has_section('Commands'):
        for command in ini_config.items("Commands"):
            if options.commands == command[0]:
                options.commands = command[1]
                break


def read_hosts(host_path):
    if ',' in host_path:
        return host_path.split(",")
    
    ext = os.path.splitext(host_path)[-1]
    if not ext:
        return host_path.read()
    if '.ini' == ext:
        return load_ini(host_path)
    if '.json' == ext:
        return load_json(host_path)
    if '.yml' == ext:
        return load_yaml(host_path)
    return None
