from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from functions.time_zone import pacific_now

from ._helpers import *
from .rel_user import RelUser
from .rel_user_multi import RelUserMulti
from .rel_user_text import RelUserText
from tier import *

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    current_ohm_service_id = db.Column(db.Integer, default=None)

    @property
    def user(self):
        return self.username

    @user.setter
    def user(self, value):
        self.username = value

    username = db.Column(db.String(50), unique=True)
    email_address = db.Column(db.String(255), unique=True)
    display_name = db.Column(db.String(50), unique=True)

    group_id = db.Column(db.Integer, default=None)
    point_balance = db.Column(db.Float(Precision=64), default=0)
    credit_balance = db.Column(db.Float(Precision=64), default=0)
    donated_points = db.Column(db.Float(Precision=64), default=0)
    lifetime_points_field = db.Column('lifetime_points', db.Float(Precision=64), default=0)
    create_transaction_id = db.Column(db.Integer)
    signup_date = db.Column(UTCDateTime)
    create_time = db.Column(UTCDateTime, server_default=db.func.current_timestamp())

    tier = db.Column(db.String(50))
    last_interaction_dttm = db.Column(UTCDateTime)

    rel_users = relationship("RelUser", collection_class=attribute_mapped_collection('rel_lookup'),
                             cascade="all, delete-orphan")
    rel_user_multis = relationship("RelUserMulti", backref="user")

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self._location = None
        self._enrollment = None
        self._utility_service = None

    ####################################################################################
    #
    #   Lookup Attributes
    #

    def get_attribute(self, rel_lookup, default=None, plaintext=False, rel_user_only=False):
        rel_user = self.rel_users.get(rel_lookup.upper())
        attribute = rel_user and rel_user.attribute

        return attribute

    def get_rel_user_attribute(self, rel_lookup):
        # returns entire rel_user record, including time stamp
        return RelUser.query.filter(RelUser.user_id == self.user_id, RelUser.rel_lookup == rel_lookup).first()

    def delete_attribute(self, rel_lookup):
        rel_user = RelUser.query.filter(RelUser.user_id == self.user_id, RelUser.rel_lookup == rel_lookup).first()
        if rel_user:
            db.session.delete(rel_user)
            db.session.flush()

    def add_multi(self, rel_lookup, attribute):
        # SqlAlchemy "merge" doesn't work with secondary unique keys, so do the lookup manually
        rel_user_multi = RelUserMulti.query.filter_by(user_id=self.user_id, rel_lookup=rel_lookup, attribute=attribute).first()
        if rel_user_multi:
            rel_user_multi.create_time = pacific_now()
        else:
            rel_user_multi = RelUserMulti(user_id=self.user_id, rel_lookup=rel_lookup, attribute=attribute)
            db.session.add(rel_user_multi)
        db.session.flush()

    def get_multi(self, rel_lookup):
        rel_user_multis = RelUserMulti.query.filter(RelUserMulti.user_id == self.user_id,
                                                    RelUserMulti.rel_lookup == rel_lookup).all()

        attributes = []
        for rel_user_multi in rel_user_multis:
            attributes.append(rel_user_multi.attribute)

        return attributes

    def delete_multi(self, rel_lookup, attribute):
        if DB_READ_ONLY:
            return

        rel_user_multi = RelUserMulti.query.filter(RelUserMulti.user_id == self.user_id,
                                                   RelUserMulti.rel_lookup == rel_lookup,
                                                   RelUserMulti.attribute == attribute).first()
        if rel_user_multi:
            db.session.delete(rel_user_multi)
            db.session.flush()

    def replace_multi(self, rel_lookup, attributes):
        if DB_READ_ONLY:
            return

        RelUserMulti.query.filter(RelUserMulti.user_id == self.user_id,
                                  RelUserMulti.rel_lookup == rel_lookup).delete()
        for attribute in attributes:
            self.add_multi(rel_lookup, attribute)

    def get_text_record(self, rel_lookup):
        rel_user_text = RelUserText.query.filter(RelUserText.user_id == self.user_id,
                                                 RelUserText.rel_lookup == rel_lookup).first()
        return rel_user_text

    def get_text(self, rel_lookup):
        rel_user_text = self.get_text_record(rel_lookup)
        if rel_user_text:
            return rel_user_text.attribute
        else:
            return None

    def put_text(self, rel_lookup, attribute):
        if DB_READ_ONLY:
            return

        rel_user_text = self.get_text_record(rel_lookup)
        if rel_user_text:
            rel_user_text.attribute = attribute
        else:
            db.session.begin()
            try:
                db.session.add(RelUserText(user_id=self.user_id, rel_lookup=rel_lookup, attribute=attribute,
                                       create_time=pacific_now()))
                db.session.commit()
            except Exception, e:
                db.session.rollback()
                self.put_text(rel_lookup, attribute)

        db.session.flush()

    ####################################################################################
    #
    #   Ohm Account
    #
    def full_name(self):
        return self.display_name

    def set_display_name(self, name):
        self.display_name = name
        db.session.flush()

    def short_name(self):
        return self.display_name

    def get_points_and_dollars(self):
        points = int(self.point_balance)
        return {"points": points, "dollars": points / 100}

    def get_tier(self):
        return self.tier

    def is_below_tier(self, tier):
        return is_below(self.get_tier(), tier)
    


    # These are for Flask Login --------
    #
    # MD Oct-2014 Note: the Flask login "is_active" refers to whether this user is allowed to login.
    # It is different from the "user.active_flag" which refers to whether the user has signed up, so
    # this call always returns true
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.user_id


    def __eq__(self, other):
        '''
        Checks the equality of two `UserMixin` objects using `get_id`.
        '''
        return self.get_id() == other.get_id()

    def __ne__(self, other):
        '''
        Checks the inequality of two `UserMixin` objects using `get_id`.
        '''
        return not self.__eq__(other)

    ####################################################################################
    # Class methods ----------
    #
    @classmethod
    def last(cls):
        return cls.query.order_by(cls.user_id.desc()).first()

    @classmethod
    def get_by_email(cls, email):
        user = User.query.filter_by(email_address=email).first()

        if not user:
            user = User.query.filter_by(username=email).first()

        for rel_lookup in ('PAYPAL_EMAIL_ADDRESS'):
            if user:
                continue

            rel_user = RelUser.query.filter_by(rel_lookup=rel_lookup, attribute=email).first()

            if rel_user and rel_user.user:
                user = rel_user.user

        # if user and user.is_deleted():
        #     return None

        return user

    @classmethod
    def get_by_phone(cls, phone):
        rel_user = RelUserMulti.query.filter_by(rel_lookup='PHONE_NUMBER', attribute=phone).first()

        if rel_user and rel_user.user and not rel_user.user.is_deleted():
            return rel_user.user

        return None

    @classmethod
    def find_by_attribute(cls, rel_lookup, attribute):
        return User.query.join(RelUser).filter_by(rel_lookup=rel_lookup, attribute=attribute).first()

    @classmethod
    def get_most_recent(cls):
        rs = db.session.execute("select user.user_id, tier, display_name, point_balance, m.attribute phone from user left join rel_user_multi m on user.user_id = m.user_id order by signup_date desc")
        phone = 'phone'

        # aggregate the response and append phone numbers
        collate = {}
        for r in rs:
            d = dict(r)
            user_id = d['user_id']
            if user_id not in collate:
                collate[user_id] = d
            else:
                collate[user_id][phone]  = collate[user_id][phone] + "\n" + d[phone]

        return collate.values()[0:5]

    @classmethod
    def get_as_csv(cls, u_id):
        rs = db.session.execute("select user.user_id, tier, display_name, point_balance, m.attribute phone from user left join rel_user_multi m on user.user_id = m.user_id where user.user_id = :uid order by signup_date desc ", {'uid': u_id})
        phone = 'phone'

        collate = {}
        lines = ""
        for r in rs:
            d = dict(r)
            user_id = d['user_id']
            if user_id not in collate:
                collate[user_id] = d
            else:
                collate[user_id][phone]  = collate[user_id][phone] + " " + d[phone]
        
        lines += cls.dict_to_csv(collate.values())
        return lines
    
    @classmethod
    def dict_to_csv(cls, ds):
        
        line = ""
        for d in ds:
            for k in d:
                line += str(d[k]) + ","
            line = line[0:len(line)-1] + '\n'

        return line

  
