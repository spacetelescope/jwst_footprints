from os.path import abspath, dirname, expanduser, join


PKG_DIR = dirname(abspath(__file__))
PKG_DATA_DIR = join(PKG_DIR, 'data')
CONFIG_DIR = join(expanduser('~'), '.jwst_footprints')
CONFIG_FILE = join(CONFIG_DIR, 'config.json')
