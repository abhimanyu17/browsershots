# Copyright (C) 2006 Johann C. Rocholl <johann@browsershots.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Database interface for lock table.
"""

__revision__ = '$Rev$'
__date__ = '$Date$'
__author__ = '$Author$'

# How long may a factory work on a screenshot request?
lock_timeout = '0:01:00'

# How long will a failed screenshot be blocked from a factory?
failure_timeout = '0:01:00'

# How tall can a screenshot be, in pixels?
max_screenshot_height = 8000