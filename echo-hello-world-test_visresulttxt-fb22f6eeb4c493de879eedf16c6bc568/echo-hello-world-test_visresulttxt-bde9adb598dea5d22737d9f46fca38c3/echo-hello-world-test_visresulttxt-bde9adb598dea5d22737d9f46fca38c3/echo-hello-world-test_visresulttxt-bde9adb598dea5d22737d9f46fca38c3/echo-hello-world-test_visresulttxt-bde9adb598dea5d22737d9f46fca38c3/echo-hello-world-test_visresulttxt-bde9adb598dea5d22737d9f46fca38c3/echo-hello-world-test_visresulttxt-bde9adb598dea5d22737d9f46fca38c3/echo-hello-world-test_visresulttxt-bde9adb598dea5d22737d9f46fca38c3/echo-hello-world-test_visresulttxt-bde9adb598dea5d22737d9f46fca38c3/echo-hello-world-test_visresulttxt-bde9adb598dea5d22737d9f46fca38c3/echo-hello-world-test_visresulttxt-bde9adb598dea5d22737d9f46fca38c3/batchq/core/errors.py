####################################################################################
# Copyright (C) 2011-2012
# Troels F. Roennow, ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
####################################################################################

class BatchQException(StandardError):
    def __init__(self, *args, **kwargs):
        super(BatchQException,self).__init__(*args, **kwargs)

class BatchQFunctionException(BatchQException):
    def __init__(self, *args, **kwargs):
        super(BatchQFunctionException,self).__init__(*args, **kwargs)


class CommunicationIOException(IOError):
    def __init__(self, *args, **kwargs):
        super(CommunicationIOException,self).__init__(*args, **kwargs)

class CommunicationOSException(OSError):
    def __init__(self, *args, **kwargs):
        super(CommunicationOSException,self).__init__(*args, **kwargs)

class CommunicationWarning(FutureWarning):
    def __init__(self, *args, **kwargs):
        super(CommunicationWarning,self).__init__(*args, **kwargs)

class CommunicationEOF(EOFError):
    def __init__(self, *args, **kwargs):
        super(CommunicationEOF,self).__init__(*args, **kwargs)

class CommunicationTimeout(StandardError):
    def __init__(self, *args, **kwargs):
        super(CommunicationTimeout,self).__init__(*args, **kwargs)



class BasePipeException(StandardError):
    def __init__(self, *args, **kwargs):
        super(BasePipeException,self).__init__(*args, **kwargs)


class HashException(Exception):
    def __init__(self, msg):
        self._msg = str(msg)

    def __str__(self):
        return self._msg
