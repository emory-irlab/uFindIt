from django.shortcuts import redirect
from django.http import HttpRequest
import time
import urllib2

def httpreq(request, url):
    assert isinstance(request, HttpRequest)
    assert isinstance(url, str)
    n = url.find("/")
    if n < 0:
        host, path = url, "/"
    else:
        host, path = url[:n], url[n:]

    query_string = request.META['QUERY_STRING']

    cookies = dict(request.COOKIES)
    CLEAN_COOKIE_KEYS = ("p", )
    for key in CLEAN_COOKIE_KEYS:
        if key in cookies:
            del cookies[key]        

#    request.raw_post_data
