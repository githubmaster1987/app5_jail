from mysql_manage import db
from datetime import datetime
import config
import os

class DashboardNoResultOther(db.Model):
    __tablename__ = "dashboard_no_result_other"

    Id = db.Column(db.Integer(), primary_key=True)
    LastName = db.Column(db.String(25))
    FirstLetter = db.Column(db.String(50))
    Website = db.Column(db.String(50))
    NoCount = db.Column(db.Integer())

    def __init__(self, s_lastname, s_firstletter, s_website, s_nocount):
        self.FirstLetter        = s_firstletter
        self.LastName           = s_lastname
        self.Website            = s_website
        self.NoCount            = s_nocount

    # Return a nice JSON response
    def serialize(self):
        return {
            'lastname':             self.LastName,
            'firstname':            self.FirstLetter,
            'website':              self.Website,
            'nocount':              self.NoCount
        }