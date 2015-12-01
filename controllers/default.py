# -*- coding: utf-8 -*-

#########################################################################
## This is the Longboxes controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

# NOTE - HANDLING OF PERMISSIONS, NON-EXISTANT PAGES ETC.
#
# Currently this controller will dump the user to 'index.html' if they try something they shouldn't
# This includes if they attempt to view a comic that doesn't exist/they aren't allowed to view
# Technically, this should never happen as the URLs to get to these pages are only linked to the user when appropriate
# As such this shouldn't be a problem, but this mechanism is used in case the user tries to manually alter URLs
# For better feedback on user actions a 'you're not allowed to see this' page should be used instead

# Search form used throughout the application
search_form = FORM('Search for a comic: ', INPUT(_name='search', requires=IS_NOT_EMPTY()) ,INPUT(_type='submit', _value='Search'), _action=URL('search'), _class='form-inline')
input_controls = search_form.elements(_type='text')
for input_control in input_controls:
    input_control['_class'] = 'form-control search-input'

# Get the unfilled box ID of the user if they are logged in
if auth.user_id:
    # Get the id of this user's unfiled box
    unfiled_box = db(db.auth_user.id == auth.user_id).select().first()
    unfiled_box_id = unfiled_box.unfiled_id
else:
    unfiled_box_id = 0

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

    # If we have a search term then we will perform a search
    if request.vars.search is not None:
        # Format the search term so we can use it in queries
        search_term="%"+request.vars.search+"%"

        # Find the user's comics that match the search
        users_comics = db(((db.comics.title.like(search_term)) | (db.comics.artists.like(search_term)) | (db.comics.writers.like(search_term)) | (db.comics.publisher.like(search_term))) & (db.comics.id == db.box_contents.comic_id) & (db.box_contents.box_id == db.boxes.id) & (db.comics.user_id == db.auth_user.id) & (db.comics.user_id == auth.user_id)).select(db.comics.ALL, db.auth_user.username, groupby=db.comics.id)
        # Find public comics that match the search
        public_comics = db(((db.comics.title.like(search_term)) | (db.comics.artists.like(search_term)) | (db.comics.writers.like(search_term)) | (db.comics.publisher.like(search_term))) & (db.comics.id == db.box_contents.comic_id) & (db.box_contents.box_id == db.boxes.id) & (db.comics.user_id == db.auth_user.id) & ((db.boxes.public == True) & (db.comics.user_id != auth.user_id))).select(db.comics.ALL, db.auth_user.username, groupby=db.comics.id)

        # Set a flag to indicate we are attempting a search
        performing_search = True

        # Set the search box to the term that was searched
        search_form.vars.search = request.vars.search

        # Process the form
        if search_form.process().accepted:
            response.flash = 'form accepted'
        elif search_form.errors:
            response.flash = 'form has errors'
        
    # If we are not searching then return no results
    else:
        users_comics = dict()
        public_comics = dict()
        performing_search = False
    
    return dict(search_form=search_form,users_comics=users_comics, public_comics=public_comics, performing_search=performing_search, search_term = request.vars.search)

# Controller for the user search
def user_search():

    # Search form for searching for a user
    user_search_form = FORM('Search for a user: ', INPUT(_name='search', requires=IS_NOT_EMPTY()) ,INPUT(_type='submit', _value='Search'), _action=URL('user_search'), _class='form-inline')
    user_search_input_controls = user_search_form.elements(_type='text')
    for input_control in user_search_input_controls:
        input_control['_class'] = 'form-control search-input'

    # If we have a search term then we will perform a search
    if request.vars.search is not None:
        # Format the search term so we can use it in queries
        search_term="%"+request.vars.search+"%"

        # Find the user's that match the search
        users = db((db.auth_user.username.like(search_term)) | (db.auth_user.first_name.like(search_term)) | (db.auth_user.last_name.like(search_term))).select(db.auth_user.username, db.auth_user.id, db.auth_user.first_name, db.auth_user.last_name)
        
        # Set a flag to indicate we are attempting a search
        performing_search = True

        # Set the search box to the term that was searched
        user_search_form.vars.search = request.vars.search

        # Process the form
        if search_form.process().accepted:
            response.flash = 'form accepted'
        elif search_form.errors:
            response.flash = 'form has errors'
        
    # If we are not searching then return no results
    else:
        users = dict()
        performing_search = False

    return dict(user_search_form = user_search_form, users = users, performing_search = performing_search, search_term = request.vars.search)

# Controller for the comic viewer page
def comic():
    # Check if we have a comic id set as a GET var
    if request.get_vars.id is not None:
        # Get the comic ID to display from the GET vars
        comic_id = request.get_vars.id
        # Find the comic in the db
        comic = db((db.comics.id == comic_id) & (db.comics.user_id == db.auth_user.id)).select(db.comics.ALL, db.auth_user.username).first()
    # Otherwise do nothing and redirect to index - this should never happen!
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

        # If there are no public boxes then this user shouldn't be allowed to see this comic - this should never happen!
        if boxes == False:
            redirect(URL('index'))

    # If we have a saved GET var then we need to tell the view
    if request.get_vars.saved is not None:
        saved = True
    else:
        saved = False

    return dict(comic=comic, boxes=boxes, own_comic = own_comic, saved = saved)

# Controller to display the details of a specific box
def box():

    # If we have the ID of a box to display then we will display it
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
        
    # Otherwise we will redirect to the home page - this should never happen!
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
        # If the user isn't logged in then return then take them to the login page - useful for if they have made a bookmark to collection
        else:
            redirect(URL('user/login'))

    if int(user_id) == auth.user_id:
        # We are viewing the user's own collection
        own_collection = True

        # Set some text to describe whose collection we are viewing
        name_text = 'your own'
        title = 'Your collection'

        # Get the user's own boxes - all including public and private
        boxes = db(db.boxes.user_id==user_id).select(db.boxes.id, db.boxes.name, db.boxes.created_date, count.with_alias('number_of_comics'), groupby=db.boxes.id, orderby=db.boxes.created_date, left=db.box_contents.on(db.boxes.id==db.box_contents.box_id))

        # Get the user's comics
        comics = db((db.comics.user_id == user_id) & (db.comics.user_id == db.auth_user.id)).select(db.comics.ALL, db.auth_user.username)

    else:
        # We are viewing someone else's collection
        own_collection = False

        # Set some text to describe whose collection we are viewing
        name_text = db.auth_user[user_id].username + '\'s public'
        title = db.auth_user[user_id].username + '\'s collection'

        # Get just the user's public boxes
        boxes = db((db.boxes.user_id==user_id) & (db.boxes.public == True)).select(db.boxes.id, db.boxes.name, db.boxes.created_date, count.with_alias('number_of_comics'), groupby=db.boxes.id, orderby=db.boxes.created_date, left=db.box_contents.on(db.boxes.id==db.box_contents.box_id))

        # Get the user's public comics
        comics = db((db.comics.user_id == user_id) & (db.comics.id == db.box_contents.comic_id) & (db.box_contents.box_id == db.boxes.id) & (db.boxes.public == True) & (db.comics.user_id == db.auth_user.id)).select(db.comics.ALL, db.box_contents.ALL, db.boxes.ALL, db.auth_user.username, groupby=db.comics.id)

    # We use a URL var to specify when we display a delete confirmation alert
    if request.get_vars.deleted is not None:
        # Based on the value of the deleted URL parameter we choose what deleted text to send to the view
        deleted = request.get_vars.deleted
        if deleted == 'comic':
            deleted_text = 'The specified comic was removed from your collection'
        elif deleted == 'box':
            deleted_text = 'The specified box was removed from your collection. Any comics it contained have now been moved to the Unfiled box'
    else:
        deleted = None
        deleted_text = None

    # Check if we have saved a box, if so pass that to the view
    if request.get_vars.box_saved is not None:
        box_saved = True
    else:
        box_saved = False

    return dict(boxes = boxes, comics = comics, name_text = name_text, title = title, own_collection = own_collection, deleted = deleted, deleted_text = deleted_text, box_saved = box_saved, unfiled_box_id = unfiled_box_id)

# Controller to add a comic to your collection
def add_to_collection():

    # Make sure a user is logged in
    if auth.user_id is None:
        # Redirect the user to login
        redirect(URL('user/login'))
    else:
        # Get the id of the comic
        comic_id = request.get_vars.comic

        # Find the comic in the database
        comic = db(db.comics.id == comic_id).select(db.comics.ALL).first()

        # Add the new user's ID to the comic
        comic.update(user_id = auth.user_id)

        # Add the comic to the database
        new_comic_id = db.comics.insert(**db.comics._filter_fields(comic))

        # Now need to add this comic to the unfiled box
        db.box_contents.insert(box_id = unfiled_box_id, comic_id = new_comic_id)

        # Redirect to the collection page
        redirect(URL('manage_boxes',vars={'comic':new_comic_id,'new_comic':True}))

    return dict()

# Controller to delete a box
def delete_box():
    # Get the box id from the URL
    box_id = request.get_vars.box

    # Delete the box from the boxes table
    db(db.boxes.id == box_id).delete()

    # Delete all box_contents records for this box
    db(db.box_contents.box_id == box_id).delete()

    # Move all comics without an assignment to the unfiled box

    # Find all of this user's comics that now don't have a box
    unfiled_comics = db((db.box_contents.id == None) & (db.comics.user_id == auth.user_id)).select(db.comics.ALL, db.box_contents.ALL, left=db.box_contents.on(db.box_contents.comic_id == db.comics.id))

    # Loop through each unfiled comic and add it to the unfiled box
    for row in unfiled_comics:
        db.box_contents.insert(box_id = unfiled_box_id, comic_id = row.comics.id)
        print 'test'

    # Redirect back to the collection
    redirect(URL('collection', vars={'deleted':'box'}))

    return dict()

# Controller to delete a comic
def delete_comic():
    # Get the comic ID from the URL
    comic_id = request.get_vars.comic

    # Delete the comic from the comics table
    db(db.comics.id == comic_id).delete()

    # Delete the comic from the box_contents table
    db(db.box_contents.comic_id == comic_id).delete()

    # Redirect back to the collection
    redirect(URL('collection', vars={'deleted':'comic'}))

    return dict()

# Controller for the view that manages which boxes a comic is in
def manage_boxes():

    # If we don't have a comic ID in the URL then we can't proceed - redirect back to the collection (this should never happen)
    if request.get_vars.comic is None:
        redirect(URL('collection'))

    # Get the comic id from the url
    comic_id = request.get_vars.comic

    test = request.post_vars

    # If we have POSTed the form then we need to assign the comics to the boxes
    if request.post_vars:

        # Delete all box_contents records for this comic, we will make new ones
        db(db.box_contents.comic_id == comic_id).delete()

        # Loop through each of the vars in the post request. Each of these represents a box id that this comic should be placed in
        for checkbox in request.post_vars:
            # If we have sent the data 'unfiled' then we add the comic to the unfiled box
            if checkbox == 'unfiled':
                db.box_contents.insert(box_id = unfiled_box_id, comic_id = comic_id)
            # Otherwise we add it to the specified box(es)
            else:
                db.box_contents.insert(box_id = checkbox, comic_id = comic_id)

        # Set a flag to say we have completed the update
        updated = True

    else:
        # Set a flag to say we have not performed an update
        updated = False

    # Get information about the comic we are managing
    comic = db((db.comics.id == comic_id) & (db.comics.user_id == db.auth_user.id)).select(db.comics.ALL, db.auth_user.username).first()

    # Get all of the boxes owned by this user
    boxes = db(db.boxes.user_id == auth.user_id).select(db.boxes.ALL, db.box_contents.ALL, left=db.box_contents.on((db.boxes.id == db.box_contents.box_id) & (db.box_contents.comic_id == comic_id)), orderby=db.boxes.created_date)

    # Check if this is a comic we have just added
    if request.get_vars.new_comic is not None:
        new_comic = True
    else:
        new_comic = False
    
    return dict(comic = comic, boxes = boxes, updated = updated, new_comic = new_comic)

def remove_from_box():

    if request.get_vars.box is not None and request.get_vars.comic is not None:
        # Get the box id
        box_id = request.get_vars.box

        # Get the comic id
        comic_id = request.get_vars.comic

        # Remove from the box in the db
        db((db.box_contents.comic_id == comic_id) & (db.box_contents.box_id == box_id)).delete()

        # Check if there are any records left in box contents for this comic
        boxes = db(db.box_contents.comic_id == comic_id).select()

        # If there are no records add the comic to the unfiled box
        if not boxes:
            db.box_contents.insert(box_id = unfiled_box_id, comic_id = comic_id)

    # Redirect to the page that sent the request
    redirect(request.env.http_referer)

    return dict()

def update_comic():

    # If we have a comic ID then we show an update form, otherwise we show an insert form

    #Update form
    if request.get_vars.comic is not None:
        # Get the comic ID we want to work on
        comic_id = int(request.get_vars.comic)
        # Find the comic in the db
        record = db.comics(comic_id)

        # Build the form
        form = SQLFORM(db.comics, record,formstyle='bootstrap3_stacked',fields=['title','cover','issue_number','writers','artists','publisher','description'],showid=False)
    # Insert form
    else:
        # Build the form
        form = SQLFORM(db.comics,formstyle='bootstrap3_stacked',fields=['title','cover','issue_number','writers','artists','publisher','description'])
        # We can set user_id directly
        form.vars.user_id = auth.user_id

    # Process the response from the form and display the relevant message
    if form.process().accepted:
        response.flash = 'Comic saved!'
        # Redirect to the comic page if the changes were successful
        redirect(URL('comic',vars={'id':form.vars.id,'saved':True}))

    elif form.errors:
        response.flash = 'The form has errors'

    return dict(form = form)

def update_box():
    # If we have a box ID then we show an update form, otherwise we show an insert form

    #Update form
    if request.get_vars.box is not None:
        # Get the box ID to work on
        box_id = int(request.get_vars.box)
        # Find the record in the db
        record = db.boxes(box_id)

        # Build the form
        form = SQLFORM(db.boxes, record,fields=['name','public'],formstyle='bootstrap3_stacked',showid=False)
    # Insert form
    else:
        # Build the form
        form = SQLFORM(db.boxes,fields=['name','public'],formstyle='bootstrap3_stacked')
        # We can set created_date and user_id directly        
        form.vars.created_date = request.now
        form.vars.user_id = auth.user_id

    # Process the response from the form and display the relevant message
    if form.process().accepted:
        response.flash = 'Box saved!'
        # Redirect to the collection page if the changes were successful
        redirect(URL('collection',vars={'box_saved':True}))
    elif form.errors:
        response.flash = 'The form has errors'

    return dict(form = form)

# STANDARD CONTROLLER COMPONENTS AS PROVIDED BY WEB2PY
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

    # Custom section to hide certain fields on user registration
    # This code is from - https://groups.google.com/forum/#!topic/web2py/N9CbNvFneZ8
    if 'register' in request.args or 'profile' in request.args:
        fields_to_hide = ['unfiled_id']
        for fieldname in fields_to_hide:
            field = db.auth_user[fieldname]
            field.readable = field.writable = False
            
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


