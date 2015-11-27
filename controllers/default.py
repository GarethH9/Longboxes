# -*- coding: utf-8 -*-

#########################################################################
## This is the Longboxes controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

# Search form used throughout the application
search_form = FORM('Search for a comic: ',INPUT(_name='search', requires=IS_NOT_EMPTY()) ,INPUT(_type='submit', _value='Search'), _action=URL('search'))

# Controller for the home page (index)
def index():
    # Count the number of comics in each box in the db
    count = db.box_contents.comic_id.count()

    # Find the 5 larges public boxes in the db
    largest_boxes=db((db.boxes.public==True) & (db.boxes.user_id == db.auth_user.id)).select(db.boxes.ALL, db.auth_user.username, count.with_alias('number_of_comics'), groupby=db.boxes.id, orderby=~count, limitby=(0, 5), left=db.box_contents.on(db.boxes.id==db.box_contents.box_id))

    # Find the 5 newest public boxes in the db
    newest_boxes=db((db.boxes.public==True) & (db.boxes.user_id == db.auth_user.id)).select(db.boxes.ALL, db.auth_user.username, count.with_alias('number_of_comics'), groupby=db.boxes.id, orderby=~db.boxes.created_date, limitby=(0, 5), left=db.box_contents.on(db.boxes.id==db.box_contents.box_id))

    # Return everything we need on the page
    return dict(form=search_form, largest_boxes=largest_boxes, newest_boxes=newest_boxes)

# Controller for the search page
def search():

    if request.vars.search is not None:
        search_term="%"+request.vars.search+"%"
        results = db((db.comics.title.like(search_term)) & (db.comics.id == db.box_contents.comic_id) & (db.box_contents.box_id == db.boxes.id) & ((db.comics.user_id == auth.user_id) | (db.boxes.public == True))).select(groupby=db.comics.id)
    else:
        results = dict()
    
    return dict(form=search_form,comics=results)

# Controller for the comic viewer page
def comic():
    # Check if we have a comic id set as a GET var
    if request.get_vars.id is not None:
        # Get the comic ID to display from the GET vars
        comic_id = request.get_vars.id
        # Find the comic in the db
        comic = db((db.comics.id == comic_id) & (db.comics.user_id == db.auth_user.id)).select(db.comics.ALL, db.auth_user.username).first()
    # Otherwise do nothing and redirect to index
    else:
        comic = dict()
        redirect(URL('index'))

    # If the logged in user owns this comic we will list all of the boxes it is in
    if comic.comics.user_id == auth.user_id:

        boxes = db((db.comics.id == comic_id) & (db.comics.id == db.box_contents.comic_id) & (db.box_contents.box_id == db.boxes.id) & (db.boxes.user_id == db.auth_user.id)).select()
        
        own_comic = True
    # If the logged in user doesn't own this comic we list only the public boxes
    else:
        boxes = db((db.comics.id == comic_id) & (db.boxes.public == True) & (db.comics.id == db.box_contents.comic_id) & (db.box_contents.box_id == db.boxes.id) & (db.boxes.user_id == db.auth_user.id)).select()
        own_comic = False

        # If there are no public boxes then this user shouldn't be allowed to see this comic
        if boxes == False:
            redirect(URL('index'))

    return dict(comic=comic, boxes=boxes, own_comic = own_comic)

# Controller to display the details of a specific box
def box():

    if request.get_vars.id is not None:
        box_id = request.get_vars.id

        # Get some information about the box we are viewing
        box = db((db.boxes.id == box_id) & (db.boxes.user_id == db.auth_user.id)).select(db.boxes.ALL, db.auth_user.username).first()

        # Check to make sure this user has permissions to look at this box
        if (box.boxes.public == False) & (box.boxes.user_id != auth.user_id):
            # Stop the user looking at this box
            redirect(URL('index'))

        # Get all the comics in the box
        comics = db((db.box_contents.box_id == box_id) & (db.comics.id==db.box_contents.comic_id) & (db.comics.user_id == db.auth_user.id)).select(db.comics.ALL, db.auth_user.username)

        if box.boxes.user_id == auth.user_id:
            own_box = True
        else:
            own_box = False
        
    else:
        comics = dict()
        redirect(URL('index'))
    
    return dict(comics=comics, box = box, own_box = own_box)

# Controller to display a users collection (in terms of boxes etc.)
def collection():

    # Count the number of comics in each box in the db
    count = db.box_contents.comic_id.count()

    # Check to see if we have a user ID as a GET var, if we do then store it    
    if request.get_vars.user is not None:
        user_id = request.get_vars.user
    # Otherwise we just use the current user's ID
    else:
        if auth.user_id is not None:
            user_id = auth.user_id
        else:
            redirect(URL('index'))

    if int(user_id) == int(auth.user_id):
        # We are viewing the user's own collection
        own_collection = True

        # Set some text to describe whose collection we are viewing
        name_text = 'your own'
        title = 'Your collection'

        # Get the user's own boxes - all including public and private
        boxes = db(db.boxes.user_id==user_id).select(db.boxes.id, db.boxes.name, db.boxes.created_date, count.with_alias('number_of_comics'), groupby=db.boxes.id, orderby=~count, left=db.box_contents.on(db.boxes.id==db.box_contents.box_id))

        # Get the user's comics
        comics = db((db.comics.user_id == user_id) & (db.comics.user_id == db.auth_user.id)).select(db.comics.ALL, db.auth_user.username)

    else:
        # We are viewing someone else's collection
        own_collection = False

        # Set some text to describe whose collection we are viewing
        name_text = db.auth_user[user_id].username + '\'s public'
        title = db.auth_user[user_id].username + '\'s collection'

        # Get just the user's public boxes
        boxes = db((db.boxes.user_id==user_id) & (db.boxes.public == True)).select(db.boxes.id, db.boxes.name, db.boxes.created_date, count.with_alias('number_of_comics'), groupby=db.boxes.id, orderby=~count, left=db.box_contents.on(db.boxes.id==db.box_contents.box_id))

        # Get the user's public comics
        comics = db((db.comics.user_id == user_id) & (db.comics.id == db.box_contents.comic_id) & (db.box_contents.box_id == db.boxes.id) & (db.boxes.public == True)).select(db.comics.ALL, db.box_contents.ALL, db.boxes.ALL, groupby=db.comics.id)

    return dict(boxes = boxes, comics = comics, name_text = name_text, title = title, own_collection = own_collection)

def update_comic():

    # Check if we have a comic ID passed into the form
    if request.get_vars.comic is not None:
        comic_id = int(request.get_vars.comic)
        record = db.comics(comic_id)

        form = SQLFORM(db.comics, record)
    else:
        form = SQLFORM(db.comics)

    if form.process().accepted:
        response.flash = 'form accepted'

    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'

    return dict(form = form)

def update_box():
    # Check if we have a box ID passed into the form
    if request.get_vars.box is not None:
        box_id = int(request.get_vars.box)
        record = db.boxes(box_id)

        form = SQLFORM(db.boxes, record)
    else:
        form = SQLFORM(db.boxes)

    if form.process().accepted:
        response.flash = 'form accepted'

    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'

    return dict(form = form)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


