from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import urllib
from app import db

class Miniduser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    orcid = db.Column(db.String(19))
    email = db.Column(db.String(255), unique=True)
    code = db.Column(db.String(255), unique=True)

    def __init__(self, name, orcid, email, code):
        self.name = name
        self.orcid = orcid
        self.email = email
        self.code = code

    def get_json(self):
        return {"name" : self.name, "orcid" : self.orcid, "email" : self.email }

    def __repr__(self):
        return '<User %r>' % self.name

class Entity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(120), unique=True)
    checksum = db.Column(db.String(120))
    equivalence_hash = db.Column(db.String(120))
    created = db.Column(db.DateTime())
    status = db.Column(db.String(120))
    obsoleted_by = db.Column(db.String(120))
    miniduser_id = db.Column(db.Integer, db.ForeignKey('miniduser.id'))
    miniduser = db.relationship('Miniduser',
            backref=db.backref('entities', lazy='joined'))

    def __init__(self, miniduser, identifier, checksum, created, status, equivalence_hash):
        self.miniduser = miniduser
        self.identifier = identifier
        self.checksum = checksum
        self.created = created
        self.status = status
        self.equivalence_hash = equivalence_hash

    def get_json(self):
        u = self.miniduser.get_json()
        json = {
                "identifier" : self.identifier,
                "status" : self.status,
                "checksum" : self.checksum, 
                "equivalence_hash" : self.equivalence_hash,
                "created" : self.created,
                "obsoleted_by": self.obsoleted_by,
                "creator": u["name"],
                "orcid" : u["orcid"],
                "titles" : [],
                "locations" : []}

        for t in self.titles:
            json["titles"].append(t.get_json())
        for d in self.locations:
            json["locations"].append(d.get_json())
        return json

    def __repr__(self):
        return '<Object %r>' % self.identifier

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uri = db.Column(db.String(255))
    created = db.Column(db.DateTime())

    miniduser_id = db.Column(db.Integer, db.ForeignKey('miniduser.id'))
    miniduser = db.relationship('Miniduser',
                    backref=db.backref('locations', lazy='dynamic'))

    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'))
    entity = db.relationship('Entity',
                    backref=db.backref('locations', lazy='joined'))

    def __init__(self, entity, miniduser, uri, created):
        self.entity = entity
        self.miniduser = miniduser
        self.uri = uri
        self.created = created

    def get_json(self):
        link = self.uri
        if link and not link.startswith("http"):
            ep = self.uri.rsplit('/',1)[0]
            link = "https://www.globus.org/xfer/StartTransfer?origin=%s" % urllib.quote(ep)
        return {"uri" : self.uri,
                "link" : link,
                "created" : self.created,
                "creator" : self.miniduser.name}

    def __repr__(self):
        return '<Location %r>' % self.uri

class Title(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    created = db.Column(db.DateTime())

    miniduser_id = db.Column(db.Integer, db.ForeignKey('miniduser.id'))
    miniduser = db.relationship('Miniduser',
                                    backref=db.backref('titles', lazy='dynamic'))

    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'))
    entity = db.relationship('Entity',
                        backref=db.backref('titles', lazy='joined'))

    def __init__(self, entity, miniduser, title, created):
        self.miniduser = miniduser
        self.entity = entity
        self.title = title
        self.created = created

    def get_json(self):
        return {"title" : self.title, 
                "created" : self.created, 
                "creator": self.miniduser.name}

    def __repr__(self):
        return '<Title %r>' % self.title
