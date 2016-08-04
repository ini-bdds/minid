import sys
import os
import requests
import logging
import hashlib
import json

if sys.version_info > (3,):
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser

DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.minid')
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_PATH, 'minid-config.cfg')

logger = logging.getLogger(__name__)


def configure_logging(level=logging.INFO, logpath=None):
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    if logpath:
        logging.basicConfig(filename=logpath, level=level, format=log_format)
    else:
        logging.basicConfig(level=level, format=log_format)


def parse_config(config_file):
    if config_file == DEFAULT_CONFIG_FILE and not os.path.isfile(config_file):
        logger.info("No default configuration file found, creating one")
        create_default_config()
    config = ConfigParser()
    config.read(config_file)
    return dict(config.items('general'))


def create_default_config():
    if not os.path.isdir(DEFAULT_CONFIG_PATH):
        os.makedirs(DEFAULT_CONFIG_PATH)
    with open(DEFAULT_CONFIG_FILE, 'w') as config_file:
        config_file.writelines(['[general]\n',
                                'minid_server: http://minid.bd2k.org/minid\n',
                                'email: \n',
                                'orcid: \n',
                                'code: \n'])
    config_file.close()


def compute_checksum(file_path, algorithm=hashlib.sha256(), block_size=65536):
    logger.info("Computing checksum for %s using %s" % (file_path, algorithm))
    with open(os.path.abspath(file_path), 'rb') as open_file:
        buf = open_file.read(block_size)
        while len(buf) > 0:
            algorithm.update(buf)
            buf = open_file.read(block_size)
    open_file.close()
    return algorithm.hexdigest()


def get_entities(server, name, test):
    logger.info("Checking if the %sentity %s already exists on the server: %s" %
                ("TEST " if test else "", name, server))
    query = ""
    if test:
        query = "?test=true"
    r = requests.get("%s/%s%s" % (server, name, query), headers={"Accept": "application/json"})
    if r.status_code == 404:
        return None
    return r.json()


def create_entity(server, entity):
    r = requests.post(server, json=entity, headers={"Accept": "application/json"})
    if r.status_code in [200, 201]:
        return r.json()
    else: 
        logger.error("Error creating entity (%s) -- check parameters or config file for invalid values" % r.status_code)


def entity_json(email, code, checksum, locations, title, test, equivalence_hash):
    entity = {"email":  email, "code": code, "checksum": checksum}
    if test:
        entity["test"] = test
    if locations:
        entity["locations"] = locations
    if title: 
        entity["title"] = title
    if equivalence_hash:
        entity["equivalence_hash"] = equivalence_hash
    return entity


def print_entity(entity, as_json):
    if as_json:
        print(json.dumps(entity))
    else:
        print("Identifier: %s" % entity["identifier"])
        print("Created by: %s (%s)" % (entity["creator"], entity["orcid"]))
        print("Created: %s" % entity["created"])
        print("Checksum: %s" % entity["checksum"])

        if entity["equivalence_hash"]:
            print ("Equivalence Hash: %s" % entity["equivalence_hash"])

        print("Status: %s" % entity["status"])
        if entity["obsoleted_by"]:
            print("Obsoleted by: %s" % entity["obsoleted_by"])
        print("Locations:")
        for l in entity["locations"]:
            print("  %s - %s" % (l["creator"], l["uri"]))
        print("Title:")
        for t in entity["titles"]:
            print("  %s - %s" % (t["creator"], t["title"]))

def print_entities(entities, as_json):
    for i, entity in entities.items():
        print_entity(entity, as_json)
        print("\n")

def register_user(server, email, name, orcid):
    logger.info("Registering new user \"%s\" with email \"%s\"%s" %
                (name, email, format(" and orcid \"%s\"" % orcid) if orcid else ""))
    user = {"name": name, "email": email}
    if orcid:
        user["orcid"] = orcid
    r = requests.post("%s/user" % server, json=user, headers={"Content-Type": "application/json"})
    return r.json()


def register_entity(server, checksum, email, code, url=None, title='', test=False, equivalence_hash=None):
    logger.info("Creating new identifier")

    result = create_entity(server, entity_json(email, code, checksum, url, title, test, equivalence_hash))

    if result:
        logger.info("Created/updated minid: %s" % result["identifier"])
        return result["identifier"]

def update_entity(server, name, entity, email, code):
    if not entity:
        logger.info("No entity found to update")
        return None

    entity['email'] = email
    entity['code'] = code

    r=requests.put("%s/%s" % (server, name), json=entity, headers={"Accept": "application/json"})

    if r.status_code in [200, 201]:
        return r.json()
    else:
        logger.error("Error updating entity (%s, %s) -- check parameters or config file for invalid values" % (r.status_code, r.text))

