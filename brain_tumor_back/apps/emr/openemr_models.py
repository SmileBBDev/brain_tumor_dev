from django.db import models

class OpenEMRBaseModel(models.Model):
    class Meta:
        abstract = True
        managed = False
        app_label = 'openemr_db'  # Used by the router to direct queries

class PatientData(OpenEMRBaseModel):
    # Mapping to 'patient_data' table
    id = models.BigIntegerField(primary_key=True)
    pid = models.BigIntegerField()
    pubpid = models.CharField(max_length=255)
    
    fname = models.CharField(max_length=255)
    lname = models.CharField(max_length=255)
    mname = models.CharField(max_length=255, blank=True)
    
    DOB = models.DateField(db_column='DOB')
    sex = models.CharField(max_length=255)
    
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=255)
    country_code = models.CharField(max_length=255)
    
    phone_home = models.CharField(max_length=255)
    phone_cell = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    
    regdate = models.DateTimeField(auto_now_add=True) # Assuming auto_now_add might not work perfectly with legacy, but decent default
    last_updated = models.DateTimeField(auto_now=True)
    
    title = models.CharField(max_length=255, blank=True)
    language = models.CharField(max_length=255, default='korean')
    financial = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=255, default='active')
    
    # HIPAA & Privacy
    hipaa_mail = models.CharField(max_length=255, default='YES')
    hipaa_voice = models.CharField(max_length=255, default='YES')
    hipaa_notice = models.CharField(max_length=255, default='YES')
    hipaa_message = models.CharField(max_length=255, blank=True)
    hipaa_allowsms = models.CharField(max_length=255, default='YES')
    hipaa_allowemail = models.CharField(max_length=255, default='YES')
    
    allow_patient_portal = models.CharField(max_length=255, default='YES')
    dupscore = models.IntegerField(default=-9)

    class Meta(OpenEMRBaseModel.Meta):
        db_table = 'patient_data'


class Encounter(OpenEMRBaseModel):
    # Mapping to 'encounters' table
    # Note: 'encounter' field seems to be the logical ID in the SQL
    id = models.AutoField(primary_key=True) # Assuming 'id' exists and is PK
    date = models.DateTimeField()
    reason = models.CharField(max_length=255)
    facility_id = models.IntegerField(default=1)
    pid = models.IntegerField() # Foreign key to patient_data.pid logically
    encounter = models.IntegerField() # The encounter number
    
    last_level_all = models.IntegerField(default=0)
    last_level_closed = models.IntegerField(default=0)

    class Meta(OpenEMRBaseModel.Meta):
        db_table = 'encounters'


class Form(OpenEMRBaseModel):
    # Mapping to 'forms' table
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    encounter = models.IntegerField()
    form_name = models.CharField(max_length=255)
    form_id = models.IntegerField()
    pid = models.IntegerField()
    user = models.CharField(max_length=255)
    groupname = models.CharField(max_length=255, default='Default')
    authorized = models.IntegerField(default=1)
    deleted = models.IntegerField(default=0)

    class Meta(OpenEMRBaseModel.Meta):
        db_table = 'forms'


class Prescription(OpenEMRBaseModel):
    # Mapping to 'prescriptions' table
    id = models.AutoField(primary_key=True)
    patient_id = models.IntegerField() # pid
    drug = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    refills = models.IntegerField(default=0)
    
    start_date = models.DateField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    provider_id = models.IntegerField(default=1)
    active = models.IntegerField(default=1)
    
    txDate = models.DateField() # Transaction Date
    usage_category_title = models.CharField(max_length=255, blank=True)
    request_intent_title = models.CharField(max_length=255, blank=True)

    class Meta(OpenEMRBaseModel.Meta):
        db_table = 'prescriptions'
