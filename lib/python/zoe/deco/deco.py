# -*- coding: utf-8 -*-
#
# This file is part of Zoe Assistant - https://github.com/guluc3m/gul-zoe
#
# Copyright (c) 2013 David Muñoz Díaz <david@gul.es> 
#
# This file is distributed under the MIT LICENSE
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import zoe
import inspect

class DecoratedLogger:

    def __init__(self, listener, name, parser):
        self._listener = listener
        self._name = name
        self._parser = parser
        
    def log(self, level, msg):
        self._listener.log(self._name, level, msg, self._parser)    
    
    def info(self, msg):
        self.log("info", msg)

    def debug(self, msg):
        self.log("debug", msg)

    def warn(self, msg):
        self.log("WARNING", msg)

    def error(self, msg):
        self.log("ERROR", msg)


class DecoratedListener:
    def __init__(self, agent, name, topic):
        self._agent = agent
        self._name = name
        self._candidates = []
        self._topic = topic
        for m in dir(agent):
            k = getattr(agent, m)
            if hasattr(k, "__zoe__tags__"):
                self._candidates.append(k)
        #print("Candidates:", self._candidates)
        print("Launching agent", self._name)
        self._listener = zoe.Listener(self, name = self._name)
        if self._listener._dyn:
            self._listener.start(self.register)
        else:
            self._listener.start()

    def register(self):
        msg = { "dst":"server", 
                "tag":"register",
                "name":self._listener._name, 
                "host":self._listener._host, 
                "port":str(self._listener._port), 
                "topic":self._topic }
        m = zoe.MessageBuilder(msg).msg()
        self._listener.sendbus(m)

    def receive(self, parser):
        print("Message received:", str(parser))
        tags = parser.tags()
        self.dispatch(tags, parser)

    def dispatch(self, tags, parser):
        chosen = []
        for c in self._candidates:
            #print("  Candidate: ", c, getattr(c, '__zoe__tags__'))
            expected = c.__zoe__tags__
            #print("  Expected: ", expected)
            if self.match(tags, expected):
                #print("    Valid candidate")
                chosen.append(c)
        if len(chosen) == 0:
            print("No candidates found")
            return
        if len(chosen) > 1:
            print("Too many candidates found")
            for c in chosen:
                print(c, c.__zoe__tags__)
            return
        c = chosen[0]
        print("Candidate found:", chosen[0], "given", tags, "expected", c.__zoe__tags__)
        self.docall(c, parser)

    def match(self, tags, expected):
        #print("    Trying to match", tags, " with ", expected)
        if tags == [] and expected == []:
            # default message
            return True
        try:
            for t in expected:
                if not t in tags:
                    return False
            return True
        except Exception as e:
            return False

    def docall(self, method, parser):
        print("Calling method", method, "with parameters", parser)
        args, varargs, keywords, defaults = inspect.getargspec(method)
        if defaults:
            defaults = dict(zip(reversed(args), reversed(defaults))) # taken from http://stackoverflow.com/questions/12627118/get-a-function-arguments-default-value
        #print(defaults)
        if defaults is None:
            defaults = {}
        args = args[1:]
        params = []
        for arg in args:
            if arg == "parser":
                param = parser
            elif arg == "logger":
                param = DecoratedLogger(self._listener, self._name, parser)
            elif parser.get(arg):
                param = parser.get(arg)
            elif arg in defaults:
                param = defaults[arg]
            else:
                param = None
            params.append(param)
        self._agent.logger = DecoratedLogger(self._listener, self._name, parser)
        ret = method(*params)
        if ret:
            if not hasattr(ret, "__iter__"):
                ret = [ret]
            for r in ret:
                rep = str(r)
                print(rep)
                self._listener.sendbus(rep)

class Message:
    def __init__(self, tags):
        self._tags = tags
        #print("Message with tags", self._tags)

    def __call__(self, f):
        #print("Setting tags", self._tags, "to", f)
        setattr(f, "__zoe__tags__", self._tags)
        return f

class Agent:
    def __init__(self, name, topic = None):
        self._name = name
        self._topic = topic

    def __call__(self, i):
        DecoratedListener(i(), self._name, self._topic)

