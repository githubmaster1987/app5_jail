from mysql_manage import db
from datetime import datetime
import config
import os

class DashboardNoResult(db.Model):
    __tablename__ = "dashboard_no_result"

    Id = db.Column(db.Integer(), primary_key=True)
    LastName = db.Column(db.String(25))
    FirstLetter = db.Column(db.String(50))
    
    def __init__(self, s_lastname, s_firstletter):
        self.FirstLetter        = s_firstletter
        self.LastName           = s_lastname
        
    # Return a nice JSON response
    def serialize(self):
        return {
            'lastname':             self.LastName,
            'firstname':            self.FirstLetter,
        }