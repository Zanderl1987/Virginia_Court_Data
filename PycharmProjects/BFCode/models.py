from sqlalchemy.ext.automap import automap_base
from flask_login import UserMixin
from sandbox import db

Base = automap_base() # Automap

class Subject(Base,UserMixin):
    __tablename__ = 'subject'

Base.prepare(db.engine, reflect=True)

# Classes

BasalProfile = Base.classes.basal_profile
CFProfile = Base.classes.CF_profile
CRProfile = Base.classes.CR_profile
CGM = Base.classes.cgm
CGMDevice = Base.classes.cgm_device
Insulin = Base.classes.insulin
Meal = Base.classes.meal
ModelParameters = Base.classes.model_parameters
PumpDevice = Base.classes.pump_device
Session = Base.classes.session
#Subject = Base.classes.subject
