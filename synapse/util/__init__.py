# -*- coding: utf-8 -*-
# Copyright 2014, 2015 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from synapse.util.logcontext import LoggingContext

from twisted.internet import defer, reactor, task

import time
import logging

logger = logging.getLogger(__name__)


class Clock(object):
    """A small utility that obtains current time-of-day so that time may be
    mocked during unit-tests.

    TODO(paul): Also move the sleep() functionallity into it
    """

    def time(self):
        """Returns the current system time in seconds since epoch."""
        return time.time()

    def time_msec(self):
        """Returns the current system time in miliseconds since epoch."""
        return self.time() * 1000

    def looping_call(self, f, msec):
        l = task.LoopingCall(f)
        l.start(msec/1000.0, now=False)
        return l

    def stop_looping_call(self, loop):
        loop.stop()

    def call_later(self, delay, callback):
        current_context = LoggingContext.current_context()

        def wrapped_callback():
            LoggingContext.thread_local.current_context = current_context
            callback()
        return reactor.callLater(delay, wrapped_callback)

    def cancel_call_later(self, timer):
        timer.cancel()

    def time_bound_deferred(self, given_deferred, time_out):
        if given_deferred.called:
            return given_deferred

        ret_deferred = defer.Deferred()

        def timed_out_fn():
            try:
                ret_deferred.errback(RuntimeError("Timed out"))
            except:
                pass

            try:
                given_deferred.cancel()
            except:
                pass

        timer = None

        def cancel(res):
            try:
                self.cancel_call_later(timer)
            except:
                pass
            return res

        ret_deferred.addBoth(cancel)

        def sucess(res):
            try:
                ret_deferred.callback(res)
            except:
                pass

            return res

        def err(res):
            try:
                ret_deferred.errback(res)
            except:
                pass

            return res

        given_deferred.addCallbacks(callback=sucess, errback=err)

        timer = self.call_later(time_out, timed_out_fn)

        return ret_deferred
