# -*- coding: utf-8 -*-

from __future__ import absolute_import
import sys  

#reload(sys)  
sys.setdefaultencoding('utf8')

from .config import NUMPY_MMAP
from .onetime import OneTimeProperty, setattr_on_read
from .tmpdirs import TemporaryDirectory, InTemporaryDirectory
