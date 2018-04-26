from mysql_manage import db
from datetime import datetime
import config
import os

# Holds card information
class DashboardSandiego(db.Model):
    __tablename__ = "dashboard_sandiego_history"

    Id = db.Column(db.Integer(), primary_key=True)
    LastName = db.Column(db.String(50))
    FirstName = db.Column(db.String(50))
    MiddleName = db.Column(db.String(50))
    CapturedDate = db.Column(db.String(25))
    CapturedTime = db.Column(db.String(25))
    Duplication = db.Column(db.Integer())
    
    def __init__(self, s_lastname, s_firstname, s_middlename, s_captureddate, s_capturedtime, s_duplication):
        self.MiddleName         = s_middlename
        self.FirstName         = s_firstname
        self.LastName          = s_lastname
        self.CapturedDate      = s_captureddate
        self.CapturedTime      = s_capturedtime
        self.Duplication       = s_duplication
        
    # Return a nice JSON response
    def serialize(self):
        return {
            'middlename':           self.MiddleName,
            'lastname':             self.LastName,
            'firstname':            self.FirstName,
            'capturedate':          self.CapturedDate,
            'capturetime':          self.CapturedTime,
            'duplication':          self.Duplication
        }