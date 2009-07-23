"""
    Berd - A Twitter library for Python
    Copyright (C) 2009 Christian Blades

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import urllib2, urllib

_base_url = 'http://twitter.com/'

class Twitter():
    """Contains all of the functional methods for the Twitter API
    """

    _opener = urllib2.build_opener()
    authenticated = False
    
    def __init__(self, uname = '', pword = ''):
        """Uname and pword arguments are optional. If they exist, we'll try to authenticate using them

        Arguments:
        - 'uname': Username
        - 'pword': Password
        """
        if self.__make_opener(uname, pword):
            print "Authenticated"
            self._uname = uname
        else:
            print "Unauthenticated"

    def __make_opener(self, uname, pword):
        """Creates an opener at self.opener
        Uses basic HTTP authentication
        
        Arguments:
        - `uname`: Twitter Username
        - `pword`: Twitter Password
        """
        
        auth = urllib2.HTTPPasswordMgrWithDefaultRealm()
        auth.add_password(None, "http://twitter.com", uname, pword)
        handler = urllib2.HTTPBasicAuthHandler(auth)
        self._opener = urllib2.build_opener(handler)
        try:
            data = self._opener.open(_base_url + 'account/verify_credentials.json')
        except urllib2.HTTPError, e:
            if e.getcode == 401:
                print "401: Invalid Username or Password"
            self._opener = urllib2.build_opener()
            self.authenticated = False
            return self.authenticated
        else:
            self.authenticated = True
            return self.authenticated

    def __get_data(self, method, input_data = None):
        """Method that grabs from Twitter and spits out a dict
        
        Arguments:
        - `method`: A method from the twitter API, ie statuses/show
        - `input_data`: A dict containing the arguments
        """
        #NOTE: Need a smarter way to deal with authentication errors AND non-authentication errors. Perhaps an Error class?
        url = _base_url + method + '.json'
        if input_data == None:
            full_url = url
        else:
            input_data = urllib.urlencode(input_data)
            full_url = "?".join((url, input_data))
            
        try:
            http_data = self._opener.open(full_url)
            
        except urllib2.HTTPError, e:
            if e.getcode == 401:
                if self.get_authenticated:
                    print "Object was authenticated, but now it's not. Password changed, possibly?"
                    raise e
                print "401: Invalid Username or Password"
                print "Some Twitter methods require valid login first"
            else:
                print full_url
                raise e
            return False
        else:
            data = json.load(http_data)
            return data

    def get_authenticated(self):
        """Returns True if this object is authenticated, False otherwise
        
        """
        return self.authenticated

    def friends_timeline(self):
        """ Returns a Paginated object set for Friends Timeline
        """
        return Paginated('statuses/friends_timeline', self._opener)

    def public_timeline(self):
        """ Returns a Paginated object set for Public Timeline
        """
        return Paginated('statuses/public_timeline', self._opener)

    def user_timeline(self, user_id = None):
        """ Returns a UTimelinePaginted (Paginated) object set for an arbirary user's timeline
        """
        if user_id == None:
            return Paginated('statuses/user_timeline', self._opener)
        else:
            return UTimelinePaginated(self._opener, user_id)

    def mentions(self):
        """ Returns a Paginated object set for User's Mentions (@replies)
        """
        return Paginated('statuses/mentions')

    def set_status(self, status, in_reply_to_status_id=None):
        """Sets the user's status.
        MUST BE AUTHENTICATED

        Returns a Status object with the new status
        
        Arguments:
        - `self`:
        - `status`: String with the status message. 140 chars max
        - `in_reply_to_status_id`: Status.id of message this is a @reply to
        """
        if in_reply_to_status_id == None:
            input_data = {'status': status}
        else:
            input_data = {'status': status, 'in_reply_to_status_id': in_reply_to_status_id}

        return Status(self.__get_data('statuses/update', input_data))

    def get_status(self, status_id):
        """Retrieves a Status by ID
        
        Arguments:
        - `status_id`: Status ID
        """
        data = self.__get_data("/statuses/show/%s" % status_id)
        status = Status(data)
        return status

    def destroy_status(self, status_id):
        """Destroys a Status
        Returns a Status object containing the destroyed status
        
        Arguments:
        - `status_id`: ID of the status item to destroy
        """
        data = self.__get_data("/statuses/destroy/%s" % status_id)
        status = Status(data)
        return status

    def direct_messages(self):
        """Returns a Paginated object for the Authenticated User
        """
        
        return DirectMessagePaginated('direct_messages', self._opener)
        
    def sent_direct_messages(self):
        """ Returns a Paginated object for direct messages sent by the Authenticated User
        """
        
        return DirectMessagePaginated('direct_messages/sent', self._opener)

    def new_direct_message(self, user, text):
        """Send a direct message to User
        Returns a Direct Message object
        
        Arguments:
        - `user`: User ID or screen name
        - `text`: Text of message
        """
        input_data = {'user': user, 'text': text}
        return DirectMessage(
            self.__get_data('direct_messages/new', input_data)
            )

    def destroy_direct_message(self, id):
        """Destroys the direct message. From Twitter, not the python object
        
        Arguments:
        - `id`: DirectMessage id
        """

        return DirectMessage(
            self.__get_data('direct_messages/destroy/%s' % id)
            )

    def friendship_create(self, id, follow=True):
        """Create a new friend

        Returns new User object
        
        Arguments:
        - `id`: Screenname or ID
        - `follow`: Defaults to True
        """
        
        input_data = {'follow': follow }
        return User(
            self.__get_data('friendships/create/%s' % id, input_data)
            )

    def friendship_destroy(self, id):
        """Destroy a friendship/following

        Returns a new User object with the deleted person
        
        Arguments:
        - `id`: Screenname or ID
        """
        
        return User(
            self.__get_data('friendships/destroy/%s' % id)
            )

    def friendship_show_by_id(self, target_user_id, source_user_id = None):
        """Show a relationship between two users taking user_id as an argument
        Returns a dict with the relationship
        
        Arguments:
        - `target_user_id`: ID of the user in question
        - `source_user_id`: ID of the originating user, if None will use the Authenticated user as source
        """

        input_data = {'target_id': target_user_id}
        if not source_user_id == None:
            input_data.update({'source_id': source_user_id})
        return __get_data('friendships/show', input_data)

    def friendship_show_by_screenname(self, target_screenname, source_screenname = None):
        """Show a relationship between two users taking screenname as an argument
        Returns a dict with the relationship

        Arguments:
        - `target_screenname`: Screenname of the user in question
        - `source_screenname`: Screenname of the originating user, if None will use the Authenticated user as source
        """

        input_data = {'target_screen_name': target_screenname}
        if not source_screenname == None:
            input_data.update({'source_screen_name': source_screenname})
        return self.__get_data('friendships/show', input_data)

    def friends_ids(self):
        """Returns an array of user_ids for the Authenticated user's friends
        """

        return self.__get_data('friends/ids')

    def followers_ids(self):
        """Returns an array of user_ids for every user the Authenticated user is following
        """

        return self.__get_data('followers/ids')

    def favorites(self, page=1, screenname=None):
        """Returns an array of favorites for the specified screenname (or if None, then the Authenticated user

        20 Per page
        
        Arguments:
        - `page`: Which page to return. Defaults to the first page.
        - `screenname`: User whose favorites will be returned (if None, then the Authenticated user
        """

        input_data = {'page': page}
        if screenname == None:
            data = self.__get_data('favorites', input_data)
        else:
            data = self.__get_data('favorites/%s' % screenname, input_data)

        for x in data:
            yield Status(x)

    def favorite_create(self, id):
        """Sets status as a favorite of the Authenticated user

        Returns a Status object with the new favorite
        
        Arguments:
        - `id`: ID of the status to favorite
        """
        
        return Status(
            self.__get_data('favorites/create/%s' % id)
            )
    
    def favorite_destroy(self, id):
        """Removes this status from the Authenticated user's favorites

        Returns a Status object for the removes favorite
        
        Arguments:
        - `id`: ID of the status to remove from favorites list
        """

        return Status(
            self.__get_data('favorites/destroy/%s' % id)
            )

    def notifications_follow(self, id):
        """Enables DEVICE notifications for updates from the specified user

        Must be Authenticated

        Returns a User object
        Arguments:
        - `id`: Screenname or User ID
        """
        
        return User(
            self.__get_data('notifications/follow/%s' % id)
            )

    def notifications_leave(self, id):
        """Disables DEVICE notifications for updates from the specified user

        Must be Authenticated

        Returns a User object

        Arguments:
        - `id`: Screenname or User ID
        """

        return User(
            self.__get_data('notifications/leave/%s' % id)
            )

    def block_create(self, id):
        """Blocks the specified user (also removes from friends list

        Returns a User object
        
        Arguments:
        - `id`: Screenname or User ID
        """

        return User(
            self.__get_data('blocks/create/%s' % id)
            )

    def block_destroy(self, id):
        """Removes a block against the specified user
        
        Arguments:
        - `id`: Screenname or User ID
        """

        return User(
            self.__get_data('blocks/destroy/%s' % id)
            )

    def block_exists(self, id):
        """Tests if a block exists between the Authenticated user and the speciied user

        Returns a User object or False

        Arguments:
        - `id`: Screenname or User ID
        """

        try:
            return User(
                self.__get_data('blocks/exists/%s' % id)
                )
        except urllib2.HTTPError, e:
            if e.getcode == 404:
                return False

    def block_list(self, page = 1):
        """Returns an array of User objects, 20 per page, who the Authenticated user has blocked
        
        Arguments:
        - `page`: Defaults to 1
        """

        input_data = {'page': page}
        data = self.__get_data('blocks/blocking', input_data)
        for x in data:
            yield User(x)

    def block_ids(self):
        """Returns an array of user ids which the Authenticated user has blocked
        """

        return self.__get_data('blocks/blocking/ids')

    def rate_limit_status(self):
        """Returns the rate limit for the Authenticated User (or IP if not Authenticated)
        """

        return self.__get_data('account/rate_limit_status')

        

class Paginated():
        """Class to deal with twitter methods that take the page argument
        (as well as the since_id and max_id args)
        """
    
        def __init__(self, method, opener):
            """
            """
            self._method = method
            self._opener = opener
            self._page = 1
            self._count = 20
            self._last_id = None
            self._url = _base_url + self._method + '.json'

        def set_count(self, count):
            """ Sets the number of results per page
            """
            
            # Do some checking to make sure we don't go over Twitter's limit
            if count > 3200:
                self.count = 3200
            elif count < 1:
                self.count = 1
            else:
                self._count = count
            return self._count

        def get_count(self):
            return self._count

        def __get_data(self, input_data=None):
            # url = _base_url + self._method + '.json'
            
            if not input_data==None:
                input_data = urllib.urlencode(input_data)
                full_url = "?".join((self._url, input_data))
            else:
                full_url = self._url
                
            try:
                http_data = self._opener.open(full_url)
            except urllib2.HTTPError, e:
                if e.getcode == 401:
                    print "401: Invalid Username or Password"
                return False
            else:
                data = json.load(http_data)
                return data

        def to_status(self, data):
            """ Uses a generator to yield a set of Statuses
            This method is to shave off a couple lines of code and make life easier when extending this class
            """
            for x in data:
                yield Status(x)

        def get_tweets(self):
            """ Use this is get a list of tweets for this method
            Will get self._count tweets no matter what, (ignores last_id)
            If you want to get the next set of tweets, use next_tweets
            """
            
            self._page = 1
            input_data = {'count': self._count}
            data = self.__get_data(input_data)
            self._last_id = data[0]['id']

            return self.to_status(data)
            # for x in data:
            #     yield Status(x)

        def next_tweets(self):
            """ This should be your main method for working with this class
            Returns all the tweets for this twitter method since the last call
            OR if this is the first time, just returns self._count tweets
            """
            
            self._page = 1
            if self._last_id == None:
                input_data = {'count': self._count}
            else:
                input_data = {'count': self._count, 'since_id': self._last_id}

            data = self.__get_data(input_data)
            # if there is a blank list, just output nothing
            try:
                last_id = data[0]['id']
            except IndexError:
                pass
            else:
                self._last_id = last_id
                # self._last_id = data[0]['id']

            return self.to_status(data)
            # for x in data:
            #     yield Status(x)

        def retrieve_page(self, page):
            """ Get an arbitrary page from this Twitter method
            """
            
            if self._last_id == None:
                input_data = {'count': self._count, 'page': page}
            else:
                input_data = {'count': self._count, 'page': page, 'max_id': self._last_id}

            data = self.__get_data(input_data)

            return self.to_status(data)
            # for x in data:
            #     yield Status(x)

        def next_page(self):
            """ Get the next page from this Twitter method
            """
            
            self._page = self._page + 1

            return self.retrieve_page(self._page)

class UTimelinePaginated(Paginated):
    def __init__(self, opener, user_id):
        method = 'statuses/user_timeline'
        self.user_id = user_id
        Paginated.__init__(self, method, opener)
        self._url = _base_url + self._method + '/' + self.user_id + '.json'


class User():
    """Class to deal with Twitter users

    user_dict variable is available for anything not stored in the class itself
    (like color preferences)
    """
    id = None
    name = None
    screen_name = None
    url = None
    profile_image_url = None
    description = None
    location = None
    
    followers_count = None
    friends_count = None

    statuses_count = None
    created_ad = None
    protected = None
    utc_offset = None

    user_dict = None

    def __init__(self, user_dict):
        """
        
        Arguments:
        - `user_dict`: Dictionary from a twitter method
        """
        self.user_dict = user_dict

        if 'user' in user_dict:
            user_dict = user_dict['user']
            
        self.id = user_dict['id']
        self.name = user_dict['name']
        self.screen_name = user_dict['screen_name']
        self.url = user_dict['url']
        self.profile_image_url = user_dict['profile_image_url']
        self.description = user_dict['description']
        self.location = user_dict['location']
        # HACK! Fix for apostrophe error in Python
        try:
            self.description = self.description.replace(u'\u2019', u'\u0027')
            self.location = self.location.replace(u'\u2019', u'\u0027')
        except AttributeError:
            pass
        # End Hack
        self.followers_count = user_dict['followers_count']
        self.friend_count = user_dict['friends_count']
        self.statuses_count = user_dict['statuses_count']
        self.created_at = user_dict['created_at']
        self.protected = user_dict['protected']
        self.utc_offset = user_dict['utc_offset']

    def __str__(self):
        return '@' + self.screen_name + ': ' + self.name

    def get_timeline(self, twitter = None):
        """Returns a Paginated object containing this user's timeline

        Called with an Authenticated Twitter object will potentially return protected statuses
        
        Arguments:
        - `twitter`: An Authenticated Twitter object (if None, will use an unauthenticated request
        """
        if twitter == None:
            return Twitter.user_timeline(self.id)
        else:
            return twitter.user_timeline(self.id)

    def friendship_create(self, twitter, follow=True):
        """Creates a friendship with this User
        
        Arguments:
        - `twitter`: Authenticated Twitter object
        - `follow`: (Defaults to True) Whether or not to follow this User also
        """
        return twitter.friendship_create(self.id, follow)

    def friendship_destroy(self, twitter):
        """Removes friendship with this User
        
        Arguments:
        - `twitter`: Authenticated Twitter object
        """
        return twitter.friendship_destroy(self.id)

    def block_create(self, twitter):
        """Blocks and removes this User from the friends list
        
        Arguments:
        - `twitter`: Authenticated Twitter object
        """
        return twitter.block_create(self.id)
    
    def block_destroy(self, twitter):
        """Removes a block against this User
        
        Arguments:
        - `twitter`: Authenticated Twitter object
        """
        return twitter.block_destroy(self.id)

    
    

            
class Status():
    """ Class to deal with Twitter statuses
    
    status_dict variable stores the original dict just in case Twitter adds more
    variables to the response
    """
    status_dict = None

    favorited = None
    truncated = None
    text = None
    created_at = None
    source = None
    in_reply_to_status_id = None
    in_reply_to_screen_name = None
    id = None
    in_reply_to_user_id = None
    user = None

    def __init__(self, status_dict):
        self.status_dict = status_dict
        
        self.favorited = status_dict['favorited']
        self.truncated = status_dict['truncated']
        self.text = status_dict['text']
        # HACK! Fix for apostrophe error in Python
        self.text = self.text.replace(u'\u2019', u'\u0027')
        self.text = self.text.replace(u'\u201c', u'\u0027')
        self.created_at = status_dict['created_at']
        self.source = status_dict['source']
        self.in_reply_to_status_id = status_dict['in_reply_to_status_id']
        self.in_reply_to_screen_name = status_dict['in_reply_to_screen_name']
        self.id = status_dict['id']
        self.in_reply_to_user_id = status_dict['in_reply_to_user_id']

        self.user = User(status_dict['user'])

    def __str__(self):
        return '@' + self.user.screen_name + ': ' + self.text

    def destroy(self):
        """Destroys this status (from Twitter, not the Python object)
        """
        return Twitter.destroy_status(self.id)

    def make_favorite(self, twitter):
        """Makes this Status a favorite of the Authenticated user
        
        Arguments:
        - `twitter`: Authenticated Twitter object
        """
        return twitter.favorite_create(self.id)

    def remove_favorite(self, twitter):
        """Removes this Status from the Authenticated user's favorites list
        
        Arguments:
        - `twitter`: Authenticated Twitter object
        """

        return twitter.favorite_destroy(self.id)
    

        

class DirectMessage():
    """Class to handle Twitter Direct Messages
    
    Reveals dm_dict, which contains the original dict just in case Twitter decides to add more information to the response than what this class handles
    """

    id = None
    dm_dict = None
    sender = None
    text = None
    created_at = None
    recipient = None
    
    def __init__(self, dm_dict):
        """
        
        Arguments:
        - `dm_dict`: Dict from a twitter response
        """
        self.dm_dict = dm_dict

        self.id = dm_dict['id']
        self.sender = User(dm_dict['sender'])
        self.text = dm_dict['text']
        self.created_at = dm_dict['created_at']
        self.recipient = User(dm_dict['recipient'])

    def destroy(self):
        """Destroys the direct message from Twitter, not the python object
        
        """
        Twitter.destroy_direct_message(self.id)

    def __str__(self):
        return self.sender.screen_name + ": " + self.text
    

class DirectMessagePaginated(Paginated):
    """Class to handle the timeline from Direct Messages
    """

    def __init__(self, method, opener):
        """
        
        Arguments:
        - `method`: Twitter method to use (ie: 'direct_messages/sent')
        - `opener`: OpenDirector object from Twitter class
        """
        Paginated.__init__(self, method, opener)

    def to_status(self, data):
        for x in data:
            yield DirectMessage(x)



if __name__ == '__main__':
    twit = Twitter('imagemage', 'pooppoop')
    # tline = twit.friends_timeline()
    # data = tline.next_tweets()
    # for x in data:
    #     print x
    data = twit.direct_messages()
    print data
