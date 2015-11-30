db = DAL('sqlite://longboxes.db')

# -*- coding: utf-8 -*-

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

# Function to create an unfiled box for a user when they sign up
def create_unfiled_box(form):
    user_id = form.vars.id
    unfiled_id = db.boxes.insert(user_id = form.vars.id, name = 'Unfiled', created_date = request.now, public = False)
    db(db.auth_user.id == user_id).update(unfiled_id = unfiled_id)

from gluon.tools import Auth, Service, PluginManager

auth = Auth(db)
service = Service()
plugins = PluginManager()

## Add a setting to redirect to profile on login
auth.settings.login_next = URL('collection')

## Add a setting to disable unwanted auth features
auth.settings.actions_disabled = ['retrieve_username', 'request_reset_password']

## Add a setting which will add an 'Unfiled' box for the user when they sign up
#auth.settings.register_onaccept.append(lambda form: db.boxes.insert(user_id = form.vars.id, name = 'Unfiled', created_date = request.now, public = False))
auth.settings.register_onaccept = create_unfiled_box


db.define_table(
    auth.settings.table_user_name,
    Field('first_name', length=128, default=''),
    Field('last_name', length=128, default=''),
    Field('unfiled_id'),
    Field('username', length=128, default='', unique=True), # required
    Field('password', 'password', length=512,            # required
          readable=False, label='Password'),
    Field('registration_key', length=512,                # required
          writable=False, readable=False, default=''),
    Field('reset_password_key', length=512,              # required
          writable=False, readable=False, default=''),
    Field('registration_id', length=512,                 # required
          writable=False, readable=False, default='')),

## do not forget validators
custom_auth_table = db[auth.settings.table_user_name] # get the custom_auth_table
custom_auth_table.first_name.requires =   IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.last_name.requires =   IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.password.requires = [CRYPT()]
custom_auth_table.username.requires = [
  IS_NOT_IN_DB(db, custom_auth_table.username)]

auth.settings.table_user = custom_auth_table # tell auth to use custom_auth_table

## create all tables needed by auth if not custom tables
auth.define_tables(username=True, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

#comics table
db.define_table('comics',
				Field('title', type='text', requires=IS_NOT_EMPTY()),
				Field('cover', type='upload', requires=IS_NOT_EMPTY()),
				Field('issue_number', type='integer', requires=IS_NOT_EMPTY()),
				Field('writers', type='text', requires=IS_NOT_EMPTY()),
				Field('artists', type='text', requires=IS_NOT_EMPTY()),
				Field('publisher', type='text', requires=IS_NOT_EMPTY()),
				Field('description', type='text', requires=IS_NOT_EMPTY()),
                                Field('user_id', db.auth_user, requires=IS_NOT_EMPTY()))
			
#boxes table
db.define_table('boxes',
				Field('user_id', db.auth_user),
				Field('name', type='string'),
				Field('created_date', type='datetime'),
				Field('public', type='boolean'))
			
#box_contents table
db.define_table('box_contents',
				Field('box_id', db.boxes),
				Field('comic_id', db.comics))
