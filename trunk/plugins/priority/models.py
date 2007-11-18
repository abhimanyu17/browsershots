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
Priority models.
"""

__revision__ = "$Rev$"
__date__ = "$Date$"
__author__ = "$Author$"

from django.db import models
from django.contrib.auth.models import User
from shotserver04.websites.models import Domain


class UserPriority(models.Model):
    user = models.ForeignKey(User, raw_id_admin=True)
    priority = models.IntegerField()
    expire = models.DateTimeField()

    class Admin:
        list_display = ('user', 'priority', 'expire')

    def __unicode__(self):
        return u"Priority %d for %s" % (self.priority, self.user)


class DomainPriority(models.Model):
    domain = models.ForeignKey(Domain, raw_id_admin=True)
    priority = models.IntegerField()
    expire = models.DateTimeField()

    class Admin:
        list_display = ('domain', 'priority', 'expire')

    def __unicode__(self):
        return u"Priority %d for %s" % (self.priority, self.domain)