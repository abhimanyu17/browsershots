# browsershots.org - Test your web design in different browsers
# Copyright (C) 2007 Johann C. Rocholl <johann@browsershots.org>
#
# Browsershots is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Browsershots is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
XML-RPC interface for requests app.
"""

__revision__ = "$Rev$"
__date__ = "$Date$"
__author__ = "$Author$"

from xmlrpclib import Fault
from django.db import models
from shotserver04.common import serializable
from shotserver04.xmlrpc import signature, factory_xmlrpc
from shotserver04.nonces import xmlrpc as nonces
from shotserver04.factories.models import Factory, ScreenSize, ColorDepth
from shotserver04.browsers.models import Browser
from shotserver04.requests.models import Request
from datetime import datetime, timedelta
# import time # For test_overload.py


@serializable
def find_and_lock_request(factory, features):
    """
    Find a matching screenshot request and lock it.
    """
    # Find matching request
    now = datetime.now()
    five_minutes_ago = now - timedelta(0, 300)
    matches = Request.objects.select_related()
    matches = matches.filter(features)
    matches = matches.filter(screenshot__isnull=True)
    matches = matches.filter(request_group__expire__gt=now)
    matches = matches.filter(
        models.Q(locked__isnull=True) | models.Q(locked__lt=five_minutes_ago))
    matches = matches.order_by(
        '-priority', 'requests_request__request_group.submitted')
    matches = matches[:1]
    # time.sleep(0.1) # For test_overload.py
    if len(matches) == 0:
        raise Fault(204, 'No matching request.')
    request = matches[0]
    # Lock request
    request.update_fields(factory_id=factory.id, locked=datetime.now())
    return request


def add_version(filters, value, name, exact=False):
    """
    Update filters to get the browser for a matching request.
    """
    if value is None:
        return
    if hasattr(value, 'id'):
        value = value.id
    if value == 2 and not exact: # request for 'enabled'
        filters[name + '__gte'] = 2 # match 'enabled' or version
    else:
        filters[name] = value # specific requested version


def version_or_empty(feature):
    """Return version field, or empty string if feature is None."""
    if feature is None:
        return ''
    else:
        return feature.version


@factory_xmlrpc
@signature(dict, str, str)
def poll(http_request, factory, encrypted_password):
    """
    Try to find a matching screenshot request for a given factory.

    Arguments
    ~~~~~~~~~
    * factory_name string (lowercase, normally from hostname)
    * encrypted_password string (lowercase hexadecimal, length 32)

    See nonces.verify for how to encrypt your password.

    Return value
    ~~~~~~~~~~~~
    * options dict (screenshot request configuration)

    If successful, the options dict will have the following keys:

    * request int (for redirect and screenshots.upload)
    * browser string (browser name)
    * version string (browser version)
    * major int (major browser version number)
    * minor int (minor browser version number)
    * command string (browser command to run, empty for default)
    * width int (screen width in pixels)
    * height int (screen height in pixels)
    * bpp int (color depth in bits per pixel)
    * javascript string (javascript version)
    * java string (java version)
    * flash string (flash version)

    Locking
    ~~~~~~~
    The matching screenshot request is locked for five minutes. This
    is to make sure that no requests are processed by two factories at
    the same time. If your factory takes longer to process a request,
    it is possible that somebody else will lock it. In this case, your
    upload will fail.
    """
    # Verify authentication
    nonces.verify(http_request, factory, encrypted_password)
    # Update last_poll timestamp
    factory.update_fields(last_poll=datetime.now(),
                          ip=http_request.META['REMOTE_ADDR'])
    # Get matching request
    request = find_and_lock_request(factory, factory.features_q())
    # Get matching browser
    filters = {'factory': factory,
               'browser_group': request.browser_group,
               'active': True}
    add_version(filters, request.major, 'major', exact=True)
    add_version(filters, request.minor, 'minor', exact=True)
    add_version(filters, request.request_group.javascript, 'javascript__id')
    add_version(filters, request.request_group.java, 'java__id')
    add_version(filters, request.request_group.flash, 'flash__id')
    try:
        browser = Browser.objects.select_related().get(**filters)
    except Browser.DoesNotExist:
        raise Fault(404, "No matching browser for selected request.")
    # Build result dict
    screen_size = select_screen_size(factory, request)
    color_depth = select_color_depth(factory, request)
    return {
        'request': request.id,
        'browser': browser.browser_group.name,
        'version': browser.version,
        'major': browser.major,
        'minor': browser.minor,
        'command': browser.command,
        'width': screen_size.width,
        'height': screen_size.height,
        'bpp': color_depth.bits_per_pixel,
        'javascript': version_or_empty(request.request_group.javascript),
        'java': version_or_empty(request.request_group.java),
        'flash': version_or_empty(request.request_group.flash),
        }


def select_screen_size(factory, request):
    """
    Select a matching screen size for this screenshot request.
    """
    screen_sizes = ScreenSize.objects.filter(factory=factory)
    if request.request_group.width:
        screen_sizes = screen_sizes.filter(width=request.request_group.width)
    if request.request_group.height:
        screen_sizes = screen_sizes.filter(height=request.request_group.height)
    # Fallback to default size if factory configuration incomplete
    if not len(screen_sizes):
        return ScreenSize(factory=factory, width=1024, height=768)
    # Try most popular screen sizes first
    if len(screen_sizes) > 1:
        for popular in (1024, 800, 1152, 1280, 640):
            for screen_size in screen_sizes:
                if screen_size.width == popular:
                    return screen_size
    # Return the smallest matching screen size
    return screen_sizes[0]


def select_color_depth(factory, request):
    """
    Select a matching color depth for this screenshot request.
    """
    color_depths = ColorDepth.objects.filter(factory=factory)
    color_depths = color_depths.order_by('-bits_per_pixel')
    if request.request_group.bits_per_pixel:
        color_depths = color_depths.filter(
            bits_per_pixel=request.request_group.bits_per_pixel)
    # Fallback to default depth if factory configuration incomplete
    if not len(color_depths):
        return ColorDepth(factory=factory, bits_per_pixel=24)
    # Return greatest matching color depth
    return color_depths[0]