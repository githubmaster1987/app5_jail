from mysql_manage import db
from datetime import datetime
import config
import os

# Holds card information
class DashboardLasdJail(db.Model):
    __tablename__ = "dashboard_lasd_jail"

    Id = db.Column(db.Integer(), primary_key=True)
    BookingNo = db.Column(db.String(25))
    LastName = db.Column(db.String(30))
    FirstName = db.Column(db.String(30))
    MiddleName = db.Column(db.String(30))
    Birthday = db.Column(db.String(30))
    Age = db.Column(db.String(10))
    Sex = db.Column(db.String(10))
    Race = db.Column(db.String(10))
    Hair = db.Column(db.String(20))
    Eyes = db.Column(db.String(20))
    Height = db.Column(db.String(10))
    Weight = db.Column(db.String(10))
    ArrestDate = db.Column(db.String(25))
    ArrestTime = db.Column(db.String(25))
    CapturedDate = db.Column(db.String(25))
    CapturedTime = db.Column(db.String(25))
    ArrestAgency = db.Column(db.String(25))
    AgencyDescription = db.Column(db.String(200))
    DateBooked = db.Column(db.String(25))
    TimeBooked = db.Column(db.String(25))
    BookingLocation = db.Column(db.String(50))
    LocationDescription = db.Column(db.String(200))
    TotalBailAmount = db.Column(db.String(25))
    TotalHoldBailAmount = db.Column(db.String(25))
    GrandTotal = db.Column(db.String(25))
    HousingLocation = db.Column(db.String(50))
    PermanentHousingAssignedDate = db.Column(db.String(25))
    AssignedTime = db.Column(db.String(25))
    VisitorStatus = db.Column(db.String(10))
    Facility = db.Column(db.String(45))
    Address = db.Column(db.String(45))
    City = db.Column(db.String(45))
 
    def __init__(self, s_bookingno, s_lastname, s_firstname, s_middlename, s_birthday, s_age, s_sex, s_race, s_hair, 
        s_eyes, s_height, s_weight, s_arrestdate, s_arresttime, s_captureddate, s_capturedtime, s_arrestagency, 
        s_agencydescription, s_datebooked, s_timebooked, s_bookinglocation, s_locationdescription, s_totalbailamount, 
        s_totalholdbailamount, s_grandtotal, s_housinglocation, s_permanenthousingassigneddate, s_assignedtime, 
        s_visitorstatus, s_facility, s_address, s_city):

        self.BookingNo          = s_bookingno
        self.LastName           = s_lastname
        self.FirstName          = s_firstname
        self.MiddleName         = s_middlename
        self.Birthday           = s_birthday
        self.Age                = s_age
        self.Sex                = s_sex
        self.Race               = s_race
        self.Hair               = s_hair
        self.Eyes               = s_eyes
        self.Height             = s_height
        self.Weight             = s_weight
        self.ArrestDate         = s_arrestdate
        self.ArrestTime         = s_arresttime
        self.CapturedDate       = s_captureddate
        self.CapturedTime       = s_capturedtime
        self.ArrestAgency       = s_arrestagency
        self.AgencyDescription  = s_agencydescription
        self.DateBooked         = s_datebooked
        self.TimeBooked         = s_timebooked
        self.BookingLocation    = s_bookinglocation
        self.LocationDescription = s_locationdescription
        self.TotalBailAmount    = s_totalbailamount
        self.TotalHoldBailAmount = s_totalholdbailamount
        self.GrandTotal         = s_grandtotal
        self.HousingLocation    = s_housinglocation
        self.PermanentHousingAssignedDate = s_permanenthousingassigneddate
        self.AssignedTime       = s_assignedtime
        self.VisitorStatus      = s_visitorstatus
        self.Facility           = s_facility
        self.Address            = s_address
        self.City               = s_city
        
    # Return a nice JSON response
    def serialize(self):
        return {
            'bookingno':    self.BookingNo,
            'lastname':     self.LastName,
            'firstname':    self.FirstName,
            'middlename':   self.MiddleName,
            'birthday':     self.Birthday,
            'age':          self.Age,
            'sex':          self.Sex,
            'race':         self.Race,
            'hair':         self.Hair,
            'eyes':         self.Eyes,
            'height':       self.Height,
            'weight':       self.Weight,
            'arrestdate':   self.ArrestDate,
            'arresttime':   self.ArrestTime,
            'captureddate':     self.CapturedDate,
            'capturedtime':     self.CapturedTime,
            'arrestagency':     self.ArrestAgency,
            'agencydescription':    self.AgencyDescription,
            'datebooked':           self.DateBooked,
            'timebooked':           self.TimeBooked,
            'bookinglocation':      self.BookingLocation,
            'locationdescription':  self.LocationDescription,
            'totalbailamount':      self.TotalBailAmount,
            'totalholdbailamount':  self.TotalHoldBailAmount,
            'grandtotal':           self.GrandTotal,
            'housinglocation':      self.HousingLocation,
            'permanenthousingassigneddate': self.PermanentHousingAssignedDate,
            'assignedtime':         self.AssignedTime,
            'visitorstatus':        self.VisitorStatus,
            'facility':             self.Facility,
            'address':              self.Address,
            'city':                 self.City,
        }