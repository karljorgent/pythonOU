from app import db
from datetime import datetime

class Company(db.Model):
    """Osaühingu mudel"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    registry_code = db.Column(db.String(7), unique=True, nullable=False)
    founding_date = db.Column(db.Date, nullable=False)
    share_capital = db.Column(db.Integer, nullable=False)
    shareholders = db.relationship('Shareholder', backref='company', lazy=True)

    def __repr__(self):
        return f'<Company {self.name}>'

class Person(db.Model):
    """Isiku (füüsiline või juriidiline) baasklass"""
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    company_name = db.Column(db.String(100))
    identification_code = db.Column(db.String(50), unique=True, nullable=False)
    shareholdings = db.relationship('Shareholder', backref='person', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'person',
        'polymorphic_on': type
    }

class NaturalPerson(Person):
    """Füüsilise isiku mudel"""
    __mapper_args__ = {
        'polymorphic_identity': 'natural'
    }

class LegalPerson(Person):
    """Juriidilise isiku mudel"""
    __mapper_args__ = {
        'polymorphic_identity': 'legal'
    }

class Shareholder(db.Model):
    """Osaniku mudel"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    share_size = db.Column(db.Integer, nullable=False)
    is_founder = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Shareholder {self.person_id} of {self.company_id}>'

