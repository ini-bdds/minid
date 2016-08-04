from flask import jsonify, make_response, request, render_template, abort
from models import *
import uuid
import datetime
from providers import EZIDClient
from app import app, db, minid_email

# When using the test capabilities we append TEST to the checksum to avoid 
# colusion with the real namespace
TEST_CHECKSUM_PREFIX = "TEST-"
VALID_STATUS = ["ACTIVE", "TOMBSTONE"]

def create_ark(creator, title, created, test):
    print "Creating ARK"
    if test:
        print "Using test EZID namespace"
        client = EZIDClient(app.config["TEST_EZID_SERVER"],
            app.config["TEST_EZID_USERNAME"],
            app.config["TEST_EZID_PASSWORD"],
            app.config["TEST_EZID_SCHEME"],
            app.config["TEST_EZID_SHOULDER"])
    else:
        client = EZIDClient(app.config["EZID_SERVER"], 
            app.config["EZID_USERNAME"], 
            app.config["EZID_PASSWORD"], 
            app.config["EZID_SCHEME"], 
            app.config["EZID_SHOULDER"])
   
    if title is None: 
        title = ""
    #data = {"erc.who" : creator, "erc.what" : title, "erc.when" : str(created)} 
    data= {"_profile" : "datacite", "datacite.creator" : creator, "datacite.title" :  title, 
            "datacite.publicationyear" : str(created.year),
            "datacite.publisher": "BD2K Minid"}#, "datacite.resourcetype" : "dataset"}
   
    response = client.mint_identifier(data)
    print "minted %s" % app.config["HOSTNAME"] 
    data ["_target"] = "%s/%s" % (app.config["LANDING_PAGE"], response["identifier"])
    client.update_identifier(response["identifier"], data)
    return response["identifier"]

def find_user(email, code):
    user = Miniduser.query.filter_by(email=email, code=code).first()
    if not user:
        print "User %s with code %s doesn't exist." % (email, code)
        abort(400)
    return user

def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

@app.route('/minid/landingpage/<path:path>', methods=['GET'])
def get_landingpage(path):
    test = request.args.get("test") in ["True", "true", "t", "T"]
    print "Getting landing page %s (%s)" % (path, test)
    
    entity = Entity.query.filter_by(identifier=path).first()

    if entity is None: 
        return "Could not locate entity %s" % path, 404
    if request_wants_json():
        return jsonify(entity.get_json())
    else:
        return render_template("entity.html", data=entity.get_json())

#
# Get entity by checksum or identifer.
#
@app.route('/minid/<path:path>', methods=['GET'])
def get_entity(path):
    if not request_wants_json():
        print "Only JSON repsonses are supported"

    test = request.args.get("test") in ["True", "true", "t", "T"]
    print "Getting minid %s (%s)" % (path, test)
    entities = None
    e_entities = None
    response_dict = {}

    entity = Entity.query.filter_by(identifier=path).first()
    if entity:
        response_dict[entity.identifier] = entity.get_json()
    else:
        if test:
            entities = Entity.query.filter_by(checksum="%s%s" % (TEST_CHECKSUM_PREFIX, path))
        else:
            entities = Entity.query.filter_by(checksum=path)
        e_entities = Entity.query.filter_by(equivalence_hash=path)

    if entity is None and entities is None and e_entities is None:
        return "Could not locate Minid %s" % path, 404

    if entities:
        for e in entities:
            response_dict[e.identifier] = e.get_json()
    if e_entities:
        for e in e_entities:
            response_dict[e.identifier] = e.get_json()

    return jsonify(response_dict)

# Becuase Identifiers have /s we have to update the entire entity in one
@app.route('/minid/<path:path>', methods=['PUT'])
def update_entity(path):
    if not request_wants_json():
        return "Only JSON repsonses are supported", 400

    print "Updating minid %s" % path
    if not request.json:
        return "No JSON update provided", 400

    entity = Entity.query.filter_by(identifier=path).first()
    if not entity:
        return "No minid found for %s" %(path), 400

    email = request.json["email"]
    code = request.json["code"]
    up_titles = request.json["titles"]
    up_locations = request.json["locations"]
    up_status = request.json["status"]
    up_obsoleted_by = request.json["obsoleted_by"]
    up_title = None

    if up_titles:
        if len(up_titles) > 1:
            return "Only a single title can be specified", 400
        else:
            up_title = up_titles[0]["title"]

    user = find_user(email, code)

    if user != entity.miniduser:
        return "Only the creator can update a minid", 401

    # check if we need to update the entity...  status/obsoleted_by
    if entity.status != up_status:
        if up_status not in VALID_STATUS:
             return "%s is not a valid status (%s)" % (up_status, VALID_STATUS), 400
        entity.status = up_status
    if entity.obsoleted_by != up_obsoleted_by:
        ref_entity = Entity.query.filter_by(identifier=up_obsoleted_by).first()
        if not ref_entity:
            return "The obsoleted_by minid (%s) is not a valid minid" % (up_obsoleted_by), 400
        entity.obsoleted_by = up_obsoleted_by

    # Get existing locations and titles to avoid adding duplicate
    titles = [t.title for t in entity.titles]
    locations = [l.uri for l in entity.locations]
    up_locations_flat = [l.get('uri') for l in up_locations]

    created = datetime.datetime.now()

    update_title = True
    update_locations = True

    if len(titles) == 1 and up_title in titles:
        update_title = False

    keep_locations = []
    if len(up_locations) == len(locations):
        for l in up_locations_flat:
            if l in locations:
                keep_locations.append(l)

    if len(keep_locations) == len(locations):
        update_locations = False

    # Update the title by deleting the old title and adding a new title
    if update_title:
        for t in entity.titles:
            db.session.delete(t)
        if up_title is not None:
            title = Title(entity, user, up_title, created)
            db.session.add(title)

    # Update any locations by deleting changed ones and adding new ones
    if update_locations:
        for l in entity.locations:
            if l.uri in up_locations_flat:
                up_locations_flat.remove(l.uri)
            else:
                db.session.delete(l)
        for loc in up_locations_flat:
            if loc != "":
                add_location = Location(entity, user, loc, created)
                db.session.add(add_location)

    db.session.commit()

    return jsonify({'identifier': entity.identifier}), 200

# {
#  checksum: xxx
#  location: xxx
#  title: xxx
#  email: xxx
#  code: xxx
#  test: True
# }


@app.route('/minid', methods=['GET', 'POST'])
def create_entity():
    if request.method == 'GET':
        return render_template("index.html")
    
    if not request.json:
        print "Request is not formatted as JSON %s" % request.json
        abort(400)

    if not 'checksum' in request.json:
        print "Missing checksum"
        abort(400)

    entity, title, location = None, None, None
    checksum = request.json["checksum"] 
    email = request.json["email"]
    code = request.json["code"]
    title = request.json.get("title")
    locations = request.json.get("locations")
    status = "ACTIVE"
    equiv_hash = request.json["equivalence_hash"]

    test = False
    if "test" in request.json:
        test = request.json["test"]

    created = datetime.datetime.now()

    user = find_user(email, code)

    if test:
        checksum = "%s%s" % (TEST_CHECKSUM_PREFIX, checksum)
        
    #entity = Entity.query.filter_by(checksum=checksum).first()
    #if entity:
    #    print "Entity (%s) exists" % entity.identifier
    #else:
    identifier = create_ark(user.name, title, created, test)
    print "Created new identifier %s" % str(identifier)
    entity = Entity(user, str(identifier), checksum, created, status, equiv_hash)
    db.session.add(entity)

    # Get existing locations and titles to avoid adding duplicate
    existing_titles = [t.title for t in entity.titles]
    existing_locations = [l.uri for l in entity.locations]

    if title and title not in existing_titles:
        title = Title(entity, user, title, created)
        db.session.add(title)
    
    if locations:
        for l in locations:
            if l and l not in existing_locations:
                location = Location(entity, user, l, created)
                db.session.add(location)

    db.session.commit()
    return jsonify({'identifier': entity.identifier}), 201


# Register a new user.. 
# {
#  name: xxx
#  email: xxx
#  orcid: xx
# }
@app.route('/minid/user', methods=['POST','PUT'])
def register_user():
    if not request.json:
        print "Request is not JSON"
        abort(400)

    if not 'name' in request.json or not 'email' in request.json:
        print "Malformed request missing name or email %s" % request.json
        abort(400)
                                            
    email = request.json["email"]
    name = request.json["name"]
    orcid = request.json.get("orcid")

    code = str(uuid.uuid4())

    user = Miniduser.query.filter_by(email=email).first()
    if user is None: 
        user = Miniduser(name, orcid, email, code)
        db.session.add(user)
    else: 
        print "Updating existing user."
        user.name = name
        user.orcid = orcid
        user.code = code

    db.session.commit()
    
    minid_email.send_email(email, code)

    return jsonify(user.get_json()), 201
