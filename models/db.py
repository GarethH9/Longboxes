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

from gluon.tools import Auth, Service, PluginManager

auth = Auth(db)
service = Service()
plugins = PluginManager()

## Add a setting to redirect to profile on login
auth.settings.login_next = URL('collection')

## Add a setting to disable unwanted auth features
auth.settings.actions_disabled = ['retrieve_username', 'request_reset_password']

db.define_table(
    auth.settings.table_user_name,
    Field('first_name', length=128, default=''),
    Field('last_name', length=128, default=''),
    Field('username', length=128, default='', unique=True), # required
    Field('password', 'password', length=512,            # required
          readable=False, label='Password'),
    Field('registration_key', length=512,                # required
          writable=False, readable=False, default=''),
    Field('reset_password_key', length=512,              # required
          writable=False, readable=False, default=''),
    Field('registration_id', length=512,                 # required
          writable=False, readable=False, default=''))

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
				Field('title', type='text'),
				Field('cover', type='upload'),
				Field('issue_number', type='integer'),
				Field('writers', type='text'),
				Field('artists', type='text'),
				Field('publisher', type='text'),
				Field('description', type='text'),
                                Field('user_id', db.auth_user))
			
#boxes table
db.define_table('boxes',
				Field('user_id', db.auth_user),
				Field('name', type='text'),
				Field('created_date', type='datetime'),
				Field('public', type='boolean'))
			
#box_contents table
db.define_table('box_contents',
				Field('box_id', db.boxes),
				Field('comic_id', db.comics))

#db.define_table('products', Field('name'), Field('price'), Field('format'), Field('description'), Field('publisher'))

# @IAPT: For the features we are going to set up a foreign key.  Now, remember that a foreign key equates to a 1-many
# relationship in our data model, so we will simply refer to the table that we want to match things to.  Web2Py will
# then automatically set up the foreign key for us.  Pretty simple.
#db.define_table('features', Field('product_id', db.products))
