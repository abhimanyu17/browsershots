# -*- coding: utf-8 -*-
# browsershots.org
# Copyright (C) 2006 Johann C. Rocholl <johann@browsershots.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.

"""
Show a website overview.
"""

__revision__ = '$Rev: 117 $'
__date__ = '$Date: 2006-04-08 08:51:18 +0200 (Sat, 08 Apr 2006) $'
__author__ = '$Author: johann $'

import re, cgi
from mod_python import util
from shotserver03.interface import xhtml
from shotserver03.segments import browsers, features
from shotserver03 import database

def request_is_numeric():
    """
    Check if the request URI is of the form /website/<decimal>/.
    """
    if len(req.info.options) != 1:
        return False
    return req.info.options[0].isdigit()

def request_numeric_to_int():
    """
    Get integer from request URI.
    """
    return int(req.info.options[0])

def request_numeric_to_url():
    """
    Get the URL from the database.
    """
    request_int = request_numeric_to_int()
    database.connect()
    try:
        cur.execute("SELECT url FROM website WHERE website = %s", request_int)
        result = cur.fetchone()
    finally:
        database.disconnect()
    if result is None:
        return None
    return result['url']

simple_url_match = re.compile(r'^(https?://[\w\.,:;\-\_/\?&=%]+)$').match
def redirect():
    """
    Redirect if the website address can be shown in the URL.
    """
    if not request_is_numeric():
        return False

    url = request_numeric_to_url()
    if url is None:
        return False

    match = simple_url_match(url)
    if match is None:
        return False

    location = 'http://%s/website/%s' % (req.info.uri.hostname, url)
    util.redirect(req, location)

def title():
    """Page title."""
    return "Select browsers and configuration"

def error_message(message):
    """Print an error message."""
    xhtml.write_tag_line('p', message, _class="error")

request_match = re.compile(r'(\w+)\s+(/(|intl/[\w\-]+/)website/(\S*))\s+(HTTP/[\d\.]+)$').match
def body():
    """
    Write XHTML body content.
    """
    if request_is_numeric():
        website = request_numeric_to_url()
    else:
        match = request_match(req.the_request)
        if not match:
            return error_message("Your browser sent a strange request (%s)." % req.the_request)
        website = match.group(4)
        match = simple_url_match(website)
        if website and not match:
            return error_message("The web address seems to be invalid (%s)." % website)
    if not website:
        return error_message("Website address parameter is missing.")

    website = cgi.escape(website, quote = True)
    #link = xhtml.tag('a', website, href=website, _class="ext-link")
    #xhtml.write_tag_line('p', link, _class="center bold")

    # explain = "This page will show screenshots for the web address above when they get uploaded."
    # bookmark = "To come back later, bookmark this page or simply enter the address on the front page again."
    # xhtml.write_tag_line('p', '<br />\n'.join((explain, bookmark)))

    xhtml.write_open_tag_line('form', action="/submitjobs/", method="post")
    xhtml.write_tag_line('input', _type="hidden", _name="url", value=website)
    browsers.write()
    features.write()
    xhtml.write_close_tag_line('form')

    xhtml.write_tag_line('h2', "What is this?")
    xhtml.write_tag_line('p', '\n'.join((
        "On this page you can choose browser configurations for your screenshots.",
        "At the top, select the browsers that you're interested in.",
        "The drop-down boxes let you request special features.")))
    xhtml.write_tag_line('p', '\n'.join((
        "When you click the submit button, your screenshot requests will be added to the queue.",
        "It will take a while before your screenshots will be uploaded, depending on the length of the queue.",
        "Some feature combinations are impossible.",
        "If some of your requests can't be finished within your maximum wait, they will be ignored.")))
