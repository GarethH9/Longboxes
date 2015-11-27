# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
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
    largest_boxes=db(db.boxes.public==True).select(db.boxes.id, db.boxes.name, db.boxes.created_date, count.with_alias('number_of_comics'), groupby=db.boxes.id, orderby=~count, limitby=(0, 5), left=db.box_contents.on(db.boxes.id==db.box_contents.box_id))

    # Find the 5 newest public boxes in the db
    newest_boxes=db(db.boxes.public==True).select(db.boxes.id, db.boxes.name, db.boxes.created_date, count.with_alias('number_of_comics'), groupby=db.boxes.id, orderby=~db.boxes.created_date, limitby=(0, 5), left=db.box_contents.on(db.boxes.id==db.box_contents.box_id))

    # Return everything we need on the page
    return dict(form=search_form, largest_boxes=largest_boxes, newest_boxes=newest_boxes)

# Controller for the search page
def search():

    if request.vars.search is not None:
        search_term="%"+request.vars.search+"%"
        results = db(db.comics.title.like(search_term)).select()
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
        comic = db(db.comics.id == request.get_vars.id).select().first()
    # Otherwise do nothing and redirect to index
    else:
        comic = dict()
        redirect(URL('index'))
        

    return dict(comic=comic)

# Controller to display the details of a specific box
def box():

    if request.get_vars.id is not None:
        box_id = request.get_vars.id
        comics = db((db.box_contents.box_id == box_id) & (db.comics.id==db.box_contents.comic_id)).select()
    else:
        comics = dict()
        redirect(URL('index'))
    
    return dict(comics=comics)

# Controller to display a users collection (in terms of boxes etc.)
def collection():

    # Count the number of comics in each box in the db
    count = db.box_contents.comic_id.count()

    if request.get_vars.user is not None:
        user_id = request.get_vars.user
    else:
        user_id = auth.user_id

    boxes = db(db.boxes.user_id==user_id).select(db.boxes.id, db.boxes.name, db.boxes.created_date, count.with_alias('number_of_comics'), groupby=db.boxes.id, orderby=~count, limitby=(0, 5), left=db.box_contents.on(db.boxes.id==db.box_contents.box_id))

    return dict(boxes = boxes)
    

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


