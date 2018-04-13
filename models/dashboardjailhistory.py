from mysql_manage import db
from datetime import datetime
import config
import os

# Holds card information
class DashboardJailHistory(db.Model):
    __tablename__ = "dashboard_jail_history"

    Id = db.Column(db.Integer(), primary_key=True)
    BookingNo = db.Column(db.String(25))
    LastName = db.Column(db.String(50))
    FirstName = db.Column(db.String(50))
    CapturedDate = db.Column(db.String(25))
    ArrestDate = db.Column(db.String(25))
    CapturedTime = db.Column(db.String(25))
    Duplication = db.Column(db.Integer())
    
    def __init__(self, s_bookingno, s_lastname, s_firstname, s_captureddate, s_capturedtime, s_duplication, s_arrestdate):
        self.BookingNo         = s_bookingno
        self.FirstName         = s_firstname
        self.LastName          = s_lastname
        self.CapturedDate      = s_captureddate
        self.CapturedTime      = s_capturedtime
        self.Duplication       = s_duplication
        self.ArrestDate        = s_arrestdate
        
    # Return a nice JSON response
    def serialize(self):
        return {
            'bookingno':           self.BookingNo,
            'lastname':             self.LastName,
            'firstname':            self.FirstName,
            'capturedate':          self.CapturedDate,
            'capturetime':          self.CapturedTime,
            'duplication':          self.Duplication,
            'arrestdate':           self.ArrestDate
        }