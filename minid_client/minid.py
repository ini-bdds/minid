#!/usr/bin/python

from argparse import ArgumentParser
import os
import minid_client_api as minid_client

# Usage 
# minid.py <file_path> --- will give you info on file if it has been registered
# minid.py <identifer> -- will give you info on identifier
# minid.py <file_path> --register --title "My file"
# minid.py <identifier> --update --title "My file" --locations "globus://file" "http://file" --status "TOMBSTONE" --obsoleted_by "ark://99999/abcd"
# minid.py --register_user --email "Email" --name "Name" [--orcid "orcid"]


def parse_cli():
    description = 'BD2K minid tool for assigning an identifier to data'
    parser = ArgumentParser(description=description)
    parser.add_argument('--register', action="store_true", help="Register the file")
    parser.add_argument('--update', action="store_true", help="Update a minid")
    parser.add_argument('--test', action="store_true", help="Run a test of this registration using the test minid namespace")
    parser.add_argument('--json', action="store_true", help="Return output as JSON")
    parser.add_argument('--server', help="Minid server")
    parser.add_argument('--title', help="Title of named file")
    parser.add_argument('--locations',  nargs='+', help="Locations for accesing the file")
    parser.add_argument('--status', help="Status of the minid (ACTIVE or TOMBSTONE)")
    parser.add_argument('--obsoleted_by', help="A minid that replaces this minid")
    parser.add_argument("--equivalence_hash", help="A hash that can be uesd to compare equivalent content")
    parser.add_argument('--config', default=minid_client.DEFAULT_CONFIG_FILE)
    parser.add_argument('--register_user', action="store_true", help="Register a new user")
    parser.add_argument('--email', help="User email address")
    parser.add_argument('--name', help="User name")
    parser.add_argument('--orcid', help="user orcid")
    parser.add_argument('--code', help="user code")
    parser.add_argument('--quiet', action="store_true", help="suppress logging output")
    parser.add_argument('filename', nargs="?", help="file or identifier to retrieve information about or register")

    return parser.parse_args()


def main():
    args = parse_cli()
    if not args.quiet:
        minid_client.configure_logging()

    config = minid_client.parse_config(args.config)

    server = config["minid_server"]
    if args.server:
        server = args.server

    entities = None

    # register a new user
    if args.register_user:
        minid_client.register_user(server, args.email, args.name, args.orcid)
        return

    # if we got this far we *must* have a filename (or identifier) arg
    if not args.filename:
        print("Either a file name or an identifier must be specified.")
        return

    # see if this file or name exists
    file_exists = os.path.isfile(args.filename)
    if file_exists:
        checksum = minid_client.compute_checksum(args.filename)
        entities = minid_client.get_entities(server, checksum, args.test)
    else:
        entities = minid_client.get_entities(server, args.filename, False)
        if entities is None:
            print("No entity registered with identifier: %s" % args.filename)
            return
   
    # register file or display info about the entity
    if args.register:
        if entities and not file_exists:
            print("You must use the --update command to update a minid")
            return
        else:
            locations = args.locations
            if locations is None or len(locations) ==0:
                if "local_server" in config:
                    locations = ["%s%s" % (config["local_server"], os.path.abspath(args.filename))]
            minid_client.register_entity(server, checksum,
                                         args.email if args.email else config["email"],
                                         args.code if args.code else config["code"],
                                         locations, args.title, args.test, args.equivalence_hash)
    elif args.update:
        if entities is None:
            print("No entity found to update. You must use a valid minid.")
            return
        elif len(entities) > 1:
            print("More than one minid identified. Please use a minid identifier")
        else:
            entity = entities.values()[0]
            if args.status:
                entity['status'] = args.status
            if args.obsoleted_by:
                entity['obsoleted_by'] = args.obsoleted_by
            if args.title:
                entity['titles'] = [{"title" : args.title}]
            if args.locations:
                locs = []
                for l in args.locations:
                    locs.append({'uri': l})
                entity['locations'] = locs

            updated_entity = minid_client.update_entity(server, args.filename, entity,
                                       args.email if args.email else config["email"],
                                       args.code if args.code else config["code"])
            print updated_entity
    else:
        if entities:
            minid_client.print_entities(entities, args.json)
        else:
            print("File is not named. Use --register to create a name for this file.")

if __name__ == '__main__':
    main()
