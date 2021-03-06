#!/usr/bin/python

"""
	Twython is an up-to-date library for Python that wraps the Twitter API.
	Other Python Twitter libraries seem to have fallen a bit behind, and
	Twitter's API has evolved a bit. Here's hoping this helps.

	TODO: OAuth, Streaming API?

	Questions, comments? ryan@venodesigns.net
"""

import http.client, urllib, urllib.request, urllib.error, urllib.parse, mimetypes, mimetools

from urllib.error import HTTPError

__author__ = "Ryan McGrath <ryan@venodesigns.net>"
__version__ = "0.6"

try:
	import simplejson
except ImportError:
	try:
		import json as simplejson
	except:
		raise Exception("Twython requires a json library to work. http://www.undefined.org/python/")

try:
	import oauth
except ImportError:
	pass

class TwythonError(Exception):
	def __init__(self, msg, error_code=None):
		self.msg = msg
		if error_code == 400:
			raise APILimit(msg)
	def __str__(self):
		return repr(self.msg)

class APILimit(TwythonError):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return repr(self.msg)

class setup:
	def __init__(self, authtype = "OAuth", username = None, password = None, oauth_keys = None, headers = None):
		self.authtype = authtype
		self.authenticated = False
		self.username = username
		self.password = password
		self.oauth_keys = oauth_keys
		if self.username is not None and self.password is not None:
			if self.authtype == "OAuth":
				self.request_token_url = 'https://twitter.com/oauth/request_token'
				self.access_token_url = 'https://twitter.com/oauth/access_token'
				self.authorization_url = 'http://twitter.com/oauth/authorize'
				self.signin_url = 'http://twitter.com/oauth/authenticate'
				# Do OAuth type stuff here - how should this be handled? Seems like a framework question...
			elif self.authtype == "Basic":
				self.auth_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
				self.auth_manager.add_password(None, "http://twitter.com", self.username, self.password)
				self.handler = urllib.request.HTTPBasicAuthHandler(self.auth_manager)
				self.opener = urllib.request.build_opener(self.handler)
				if headers is not None:
					self.opener.addheaders = [('User-agent', headers)]
				"""
				try:
					test_verify = simplejson.load(self.opener.open("http://twitter.com/account/verify_credentials.json"))
					self.authenticated = True
				except HTTPError as e:
					raise TwythonError("Authentication failed with your provided credentials. Try again? (%s failure)" % repr(e.code), e.code)
				"""
	
	# OAuth functions; shortcuts for verifying the credentials.
	def fetch_response_oauth(self, oauth_request):
		pass
	
	def get_unauthorized_request_token(self):
		pass
	
	def get_authorization_url(self, token):
		pass
	
	def exchange_tokens(self, request_token):
		pass
	
	# URL Shortening function huzzah
	def shortenURL(self, url_to_shorten, shortener = "http://is.gd/api.php", query = "longurl"):
		try:
			return urllib.request.urlopen(shortener + "?" + urllib.urlencode({query: url_to_shorten})).read()
		except HTTPError as e:
			raise TwythonError("shortenURL() failed with a %s error code." % repr(e.code))
	
	def constructApiURL(self, base_url, params):
		return base_url + "?" + "&".join(["%s=%s" %(key, value) for (key, value) in params.items()])
	
	def getRateLimitStatus(self, rate_for = "requestingIP"):
		try:
			if rate_for == "requestingIP":
				return simplejson.load(urllib.request.urlopen("http://twitter.com/account/rate_limit_status.json"))
			else:
				if self.authenticated is True:
					return simplejson.load(self.opener.open("http://twitter.com/account/rate_limit_status.json"))
				else:
					raise TwythonError("You need to be authenticated to check a rate limit status on an account.")
		except HTTPError as e:
			raise TwythonError("It seems that there's something wrong. Twitter gave you a %s error code; are you doing something you shouldn't be?" % repr(e.code), e.code)
	
	def getPublicTimeline(self):
		try:
			return simplejson.load(urllib.request.urlopen("http://twitter.com/statuses/public_timeline.json"))
		except HTTPError as e:
			raise TwythonError("getPublicTimeline() failed with a %s error code." % repr(e.code))
	
	def getFriendsTimeline(self, **kwargs):
		if self.authenticated is True:
			try:
				friendsTimelineURL = self.constructApiURL("http://twitter.com/statuses/friends_timeline.json", kwargs)
				return simplejson.load(self.opener.open(friendsTimelineURL))
			except HTTPError as e:
				raise TwythonError("getFriendsTimeline() failed with a %s error code." % repr(e.code))
		else:
			raise TwythonError("getFriendsTimeline() requires you to be authenticated.")
	
	def getUserTimeline(self, id = None, **kwargs): 
		if id is not None and ("user_id" in kwargs) is False and ("screen_name" in kwargs) is False:
			userTimelineURL = self.constructApiURL("http://twitter.com/statuses/user_timeline/" + id + ".json", kwargs)
		elif id is None and ("user_id" in kwargs) is False and ("screen_name" in kwargs) is False and self.authenticated is True:
			userTimelineURL = self.constructApiURL("http://twitter.com/statuses/user_timeline/" + self.username + ".json", kwargs)
		else:
			userTimelineURL = self.constructApiURL("http://twitter.com/statuses/user_timeline.json", kwargs)
		try:
			# We do our custom opener if we're authenticated, as it helps avoid cases where it's a protected user
			if self.authenticated is True:
				return simplejson.load(self.opener.open(userTimelineURL))
			else:
				return simplejson.load(urllib.request.urlopen(userTimelineURL))
		except HTTPError as e:
			raise TwythonError("Failed with a %s error code. Does this user hide/protect their updates? If so, you'll need to authenticate and be their friend to get their timeline."
				% repr(e.code), e.code)
	
	def getUserMentions(self, **kwargs):
		if self.authenticated is True:
			try:
				mentionsFeedURL = self.constructApiURL("http://twitter.com/statuses/mentions.json", kwargs)
				return simplejson.load(self.opener.open(mentionsFeedURL))
			except HTTPError as e:
				raise TwythonError("getUserMentions() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("getUserMentions() requires you to be authenticated.")
	
	def showStatus(self, id):
		try:
			if self.authenticated is True:
				return simplejson.load(self.opener.open("http://twitter.com/statuses/show/%s.json" % id))
			else:
				return simplejson.load(urllib.request.urlopen("http://twitter.com/statuses/show/%s.json" % id))
		except HTTPError as e:
			raise TwythonError("Failed with a %s error code. Does this user hide/protect their updates? You'll need to authenticate and be friends to get their timeline." 
				% repr(e.code), e.code)
	
	def updateStatus(self, status, in_reply_to_status_id = None):
		if self.authenticated is True:
			if len(list(status)) > 140:
				raise TwythonError("This status message is over 140 characters. Trim it down!")
			try:
				return simplejson.load(self.opener.open("http://twitter.com/statuses/update.json?", urllib.parse.urlencode({"status": status, "in_reply_to_status_id": in_reply_to_status_id})))
			except HTTPError as e:
				raise TwythonError("updateStatus() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("updateStatus() requires you to be authenticated.")
	
	def destroyStatus(self, id):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/status/destroy/%s.json", "POST" % id))
			except HTTPError as e:
				raise TwythonError("destroyStatus() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("destroyStatus() requires you to be authenticated.")
	
	def endSession(self):
		if self.authenticated is True:
			try:
				self.opener.open("http://twitter.com/account/end_session.json", "")
				self.authenticated = False
			except HTTPError as e:
				raise TwythonError("endSession failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("You can't end a session when you're not authenticated to begin with.")
	
	def getDirectMessages(self, since_id = None, max_id = None, count = None, page = "1"):
		if self.authenticated is True:
			apiURL = "http://twitter.com/direct_messages.json?page=" + page
			if since_id is not None:
				apiURL += "&since_id=" + since_id
			if max_id is not None:
				apiURL += "&max_id=" + max_id
			if count is not None:
				apiURL += "&count=" + count
			
			try:
				return simplejson.load(self.opener.open(apiURL))
			except HTTPError as e:
				raise TwythonError("getDirectMessages() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("getDirectMessages() requires you to be authenticated.")
	
	def getSentMessages(self, since_id = None, max_id = None, count = None, page = "1"):
		if self.authenticated is True:
			apiURL = "http://twitter.com/direct_messages/sent.json?page=" + page
			if since_id is not None:
				apiURL += "&since_id=" + since_id
			if max_id is not None:
				apiURL += "&max_id=" + max_id
			if count is not None:
				apiURL += "&count=" + count
			
			try:
				return simplejson.load(self.opener.open(apiURL))
			except HTTPError as e:
				raise TwythonError("getSentMessages() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("getSentMessages() requires you to be authenticated.")
	
	def sendDirectMessage(self, user, text):
		if self.authenticated is True:
			if len(list(text)) < 140:
				try:
					return self.opener.open("http://twitter.com/direct_messages/new.json", urllib.parse.urlencode({"user": user, "text": text}))
				except HTTPError as e:
					raise TwythonError("sendDirectMessage() failed with a %s error code." % repr(e.code), e.code)
			else:
				raise TwythonError("Your message must not be longer than 140 characters")
		else:
			raise TwythonError("You must be authenticated to send a new direct message.")
	
	def destroyDirectMessage(self, id):
		if self.authenticated is True:
			try:
				return self.opener.open("http://twitter.com/direct_messages/destroy/%s.json" % id, "")
			except HTTPError as e:
				raise TwythonError("destroyDirectMessage() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("You must be authenticated to destroy a direct message.")
	
	def createFriendship(self, id = None, user_id = None, screen_name = None, follow = "false"):
		if self.authenticated is True:
			apiURL = ""
			if id is not None:
				apiURL = "http://twitter.com/friendships/create/" + id + ".json" + "?follow=" + follow
			if user_id is not None:
				apiURL = "http://twitter.com/friendships/create.json?user_id=" + user_id + "&follow=" + follow
			if screen_name is not None:
				apiURL = "http://twitter.com/friendships/create.json?screen_name=" + screen_name + "&follow=" + follow
			try:
				return simplejson.load(self.opener.open(apiURL))
			except HTTPError as e:
				# Rate limiting is done differently here for API reasons...
				if e.code == 403:
					raise TwythonError("You've hit the update limit for this method. Try again in 24 hours.")
				raise TwythonError("createFriendship() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("createFriendship() requires you to be authenticated.")
		
	def destroyFriendship(self, id = None, user_id = None, screen_name = None):
		if self.authenticated is True:
			apiURL = ""
			if id is not None:
				apiURL = "http://twitter.com/friendships/destroy/" + id + ".json"
			if user_id is not None:
				apiURL = "http://twitter.com/friendships/destroy.json?user_id=" + user_id
			if screen_name is not None:
				apiURL = "http://twitter.com/friendships/destroy.json?screen_name=" + screen_name
			try:
				return simplejson.load(self.opener.open(apiURL))
			except HTTPError as e:
				raise TwythonError("destroyFriendship() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("destroyFriendship() requires you to be authenticated.")
	
	def checkIfFriendshipExists(self, user_a, user_b):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/friendships/exists.json", urllib.parse.urlencode({"user_a": user_a, "user_b": user_b})))
			except HTTPError as e:
				raise TwythonError("checkIfFriendshipExists() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("checkIfFriendshipExists(), oddly, requires that you be authenticated.")
	
	def updateDeliveryDevice(self, device_name = "none"):
		if self.authenticated is True:
			try:
				return self.opener.open("http://twitter.com/account/update_delivery_device.json?", urllib.parse.urlencode({"device": device_name}))
			except HTTPError as e:
				raise TwythonError("updateDeliveryDevice() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("updateDeliveryDevice() requires you to be authenticated.")
	
	def updateProfileColors(self, **kwargs):
		if self.authenticated is True:
			try:
				return self.opener.open(self.constructApiURL("http://twitter.com/account/update_profile_colors.json?", kwargs))
			except HTTPError as e:
				raise TwythonError("updateProfileColors() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("updateProfileColors() requires you to be authenticated.")
	
	def updateProfile(self, name = None, email = None, url = None, location = None, description = None):
		if self.authenticated is True:
			useAmpersands = False
			updateProfileQueryString = ""
			if name is not None:
				if len(list(name)) < 20:
					updateProfileQueryString += "name=" + name
					useAmpersands = True
				else:
					raise TwythonError("Twitter has a character limit of 20 for all usernames. Try again.")
			if email is not None and "@" in email:
				if len(list(email)) < 40:
					if useAmpersands is True:
						updateProfileQueryString += "&email=" + email
					else:
						updateProfileQueryString += "email=" + email
						useAmpersands = True
				else:
					raise TwythonError("Twitter has a character limit of 40 for all email addresses, and the email address must be valid. Try again.")
			if url is not None:
				if len(list(url)) < 100:
					if useAmpersands is True:
						updateProfileQueryString += "&" + urllib.parse.urlencode({"url": url})
					else:
						updateProfileQueryString += urllib.parse.urlencode({"url": url})
						useAmpersands = True
				else:
					raise TwythonError("Twitter has a character limit of 100 for all urls. Try again.")
			if location is not None:
				if len(list(location)) < 30:
					if useAmpersands is True:
						updateProfileQueryString += "&" + urllib.parse.urlencode({"location": location})
					else:
						updateProfileQueryString += urllib.parse.urlencode({"location": location})
						useAmpersands = True
				else:
					raise TwythonError("Twitter has a character limit of 30 for all locations. Try again.")
			if description is not None:
				if len(list(description)) < 160:
					if useAmpersands is True:
						updateProfileQueryString += "&" + urllib.parse.urlencode({"description": description})
					else:
						updateProfileQueryString += urllib.parse.urlencode({"description": description})
				else:
					raise TwythonError("Twitter has a character limit of 160 for all descriptions. Try again.")
			
			if updateProfileQueryString != "":
				try:
					return self.opener.open("http://twitter.com/account/update_profile.json?", updateProfileQueryString)
				except HTTPError as e:
					raise TwythonError("updateProfile() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("updateProfile() requires you to be authenticated.")
	
	def getFavorites(self, page = "1"):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/favorites.json?page=" + page))
			except HTTPError as e:
				raise TwythonError("getFavorites() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("getFavorites() requires you to be authenticated.")
	
	def createFavorite(self, id):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/favorites/create/" + id + ".json", ""))
			except HTTPError as e:
				raise TwythonError("createFavorite() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("createFavorite() requires you to be authenticated.")
	
	def destroyFavorite(self, id):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/favorites/destroy/" + id + ".json", ""))
			except HTTPError as e:
				raise TwythonError("destroyFavorite() failed with a %s error code." %	repr(e.code), e.code)
		else:
			raise TwythonError("destroyFavorite() requires you to be authenticated.")
	
	def notificationFollow(self, id = None, user_id = None, screen_name = None):
		if self.authenticated is True:
			apiURL = ""
			if id is not None:
				apiURL = "http://twitter.com/notifications/follow/" + id + ".json"
			if user_id is not None:
				apiURL = "http://twitter.com/notifications/follow/follow.json?user_id=" + user_id
			if screen_name is not None:
				apiURL = "http://twitter.com/notifications/follow/follow.json?screen_name=" + screen_name
			try:
				return simplejson.load(self.opener.open(apiURL, ""))
			except HTTPError as e:
				raise TwythonError("notificationFollow() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("notificationFollow() requires you to be authenticated.")
	
	def notificationLeave(self, id = None, user_id = None, screen_name = None):
		if self.authenticated is True:
			apiURL = ""
			if id is not None:
				apiURL = "http://twitter.com/notifications/leave/" + id + ".json"
			if user_id is not None:
				apiURL = "http://twitter.com/notifications/leave/leave.json?user_id=" + user_id
			if screen_name is not None:
				apiURL = "http://twitter.com/notifications/leave/leave.json?screen_name=" + screen_name
			try:
				return simplejson.load(self.opener.open(apiURL, ""))
			except HTTPError as e:
				raise TwythonError("notificationLeave() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("notificationLeave() requires you to be authenticated.")
	
	def getFriendsIDs(self, id = None, user_id = None, screen_name = None, page = "1"):
		apiURL = ""
		if id is not None:
			apiURL = "http://twitter.com/friends/ids/" + id + ".json" + "?page=" + page
		if user_id is not None:
			apiURL = "http://twitter.com/friends/ids.json?user_id=" + user_id + "&page=" + page
		if screen_name is not None:
			apiURL = "http://twitter.com/friends/ids.json?screen_name=" + screen_name + "&page=" + page
		try:
			return simplejson.load(urllib.request.urlopen(apiURL))
		except HTTPError as e:
			raise TwythonError("getFriendsIDs() failed with a %s error code." % repr(e.code), e.code)
		
	def getFollowersIDs(self, id = None, user_id = None, screen_name = None, page = "1"):
		apiURL = ""
		if id is not None:
			apiURL = "http://twitter.com/followers/ids/" + id + ".json" + "?page=" + page
		if user_id is not None:
			apiURL = "http://twitter.com/followers/ids.json?user_id=" + user_id + "&page=" + page
		if screen_name is not None:
			apiURL = "http://twitter.com/followers/ids.json?screen_name=" + screen_name + "&page=" + page
		try:
			return simplejson.load(urllib.request.urlopen(apiURL))
		except HTTPError as e:
			raise TwythonError("getFollowersIDs() failed with a %s error code." % repr(e.code), e.code)
	
	def createBlock(self, id):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/blocks/create/" + id + ".json", ""))
			except HTTPError as e:
				raise TwythonError("createBlock() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("createBlock() requires you to be authenticated.")
	
	def destroyBlock(self, id):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/blocks/destroy/" + id + ".json", ""))
			except HTTPError as e:
				raise TwythonError("destroyBlock() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("destroyBlock() requires you to be authenticated.")
	
	def checkIfBlockExists(self, id = None, user_id = None, screen_name = None):
		apiURL = ""
		if id is not None:
			apiURL = "http://twitter.com/blocks/exists/" + id + ".json"
		if user_id is not None:
			apiURL = "http://twitter.com/blocks/exists.json?user_id=" + user_id
		if screen_name is not None:
			apiURL = "http://twitter.com/blocks/exists.json?screen_name=" + screen_name
		try:
			return simplejson.load(urllib.request.urlopen(apiURL))
		except HTTPError as e:
			raise TwythonError("checkIfBlockExists() failed with a %s error code." % repr(e.code), e.code)
	
	def getBlocking(self, page = "1"):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/blocks/blocking.json?page=" + page))
			except HTTPError as e:
				raise TwythonError("getBlocking() failed with a %s error code." %	repr(e.code), e.code)
		else:
			raise TwythonError("getBlocking() requires you to be authenticated")
	
	def getBlockedIDs(self):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/blocks/blocking/ids.json"))
			except HTTPError as e:
				raise TwythonError("getBlockedIDs() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("getBlockedIDs() requires you to be authenticated.")
	
	def searchTwitter(self, search_query, **kwargs):
		searchURL = self.constructApiURL("http://search.twitter.com/search.json", kwargs) + "&" + urllib.parse.urlencode({"q": search_query})
		try:
			return simplejson.load(urllib.request.urlopen(searchURL))
		except HTTPError as e:
			raise TwythonError("getSearchTimeline() failed with a %s error code." % repr(e.code), e.code)
	
	def getCurrentTrends(self, excludeHashTags = False):
		apiURL = "http://search.twitter.com/trends/current.json"
		if excludeHashTags is True:
			apiURL += "?exclude=hashtags"
		try:
			return simplejson.load(urllib.urlopen(apiURL))
		except HTTPError as e:
			raise TwythonError("getCurrentTrends() failed with a %s error code." % repr(e.code), e.code)
	
	def getDailyTrends(self, date = None, exclude = False):
		apiURL = "http://search.twitter.com/trends/daily.json"
		questionMarkUsed = False
		if date is not None:
			apiURL += "?date=" + date
			questionMarkUsed = True
		if exclude is True:
			if questionMarkUsed is True:
				apiURL += "&exclude=hashtags"
			else:
				apiURL += "?exclude=hashtags"
		try:
			return simplejson.load(urllib.urlopen(apiURL))
		except HTTPError as e:
			raise TwythonError("getDailyTrends() failed with a %s error code." % repr(e.code), e.code)
	
	def getWeeklyTrends(self, date = None, exclude = False):
		apiURL = "http://search.twitter.com/trends/daily.json"
		questionMarkUsed = False
		if date is not None:
			apiURL += "?date=" + date
			questionMarkUsed = True
		if exclude is True:
			if questionMarkUsed is True:
				apiURL += "&exclude=hashtags"
			else:
				apiURL += "?exclude=hashtags"
		try:
			return simplejson.load(urllib.urlopen(apiURL))
		except HTTPError as e:
			raise TwythonError("getWeeklyTrends() failed with a %s error code." % repr(e.code), e.code)
	
	def getSavedSearches(self):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/saved_searches.json"))
			except HTTPError as e:
				raise TwythonError("getSavedSearches() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("getSavedSearches() requires you to be authenticated.")
	
	def showSavedSearch(self, id):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/saved_searches/show/" + id + ".json"))
			except HTTPError as e:
				raise TwythonError("showSavedSearch() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("showSavedSearch() requires you to be authenticated.")
	
	def createSavedSearch(self, query):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/saved_searches/create.json?query=" + query, ""))
			except HTTPError as e:
				raise TwythonError("createSavedSearch() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("createSavedSearch() requires you to be authenticated.")
	
	def destroySavedSearch(self, id):
		if self.authenticated is True:
			try:
				return simplejson.load(self.opener.open("http://twitter.com/saved_searches/destroy/" + id + ".json", ""))
			except HTTPError as e:
				raise TwythonError("destroySavedSearch() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("destroySavedSearch() requires you to be authenticated.")
	
	# The following methods are apart from the other Account methods, because they rely on a whole multipart-data posting function set.
	def updateProfileBackgroundImage(self, filename, tile="true"):
		if self.authenticated is True:
			try:
				files = [("image", filename, open(filename).read())]
				fields = []
				content_type, body = self.encode_multipart_formdata(fields, files)
				headers = {'Content-Type': content_type, 'Content-Length': str(len(body))}
				r = urllib.request.Request("http://twitter.com/account/update_profile_background_image.json?tile=" + tile, body, headers)
				return self.opener.open(r).read()
			except HTTPError as e:
				raise TwythonError("updateProfileBackgroundImage() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("You realize you need to be authenticated to change a background image, right?")
	
	def updateProfileImage(self, filename):
		if self.authenticated is True:
			try:
				files = [("image", filename, open(filename).read())]
				fields = []
				content_type, body = self.encode_multipart_formdata(fields, files)
				headers = {'Content-Type': content_type, 'Content-Length': str(len(body))}
				r = urllib.request.Request("http://twitter.com/account/update_profile_image.json", body, headers)
				return self.opener.open(r).read()
			except HTTPError as e:
				raise TwythonError("updateProfileImage() failed with a %s error code." % repr(e.code), e.code)
		else:
			raise TwythonError("You realize you need to be authenticated to change a profile image, right?")
	
	def encode_multipart_formdata(self, fields, files):
		BOUNDARY = mimetools.choose_boundary()
		CRLF = '\r\n'
		L = []
		for (key, value) in fields:
			L.append('--' + BOUNDARY)
			L.append('Content-Disposition: form-data; name="%s"' % key)
			L.append('')
			L.append(value)
		for (key, filename, value) in files:
			L.append('--' + BOUNDARY)
			L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
			L.append('Content-Type: %s' % self.get_content_type(filename))
			L.append('')
			L.append(value)
		L.append('--' + BOUNDARY + '--')
		L.append('')
		body = CRLF.join(L)
		content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
		return content_type, body
	
	def get_content_type(self, filename):
		return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
