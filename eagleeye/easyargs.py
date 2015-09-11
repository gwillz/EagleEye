# 
# Project Eagle Eye
# Group 15 - UniSA 2015
# Gwilyn Saunders
# version 0.2.7
# 
# I didn't like getopt.
# This class separates options (--opt var) from arguments [0] => arg.
# 
# 
# Usage example in the tester script
# run tests with:
#  $ python2 easyargs.py test
#
# Special uses include compatibility with EasyConfig's config finder.
# i.e:
#   args = EasyArgs()
#   cfg = EasyConfig(args.config)
# args.config will return False if not found, causing EasyConfig to 
# start instead search the working directory for a config file.
# 
# Cheeky special use - default values.
# i.e:
#   time = args.time or 180 
# If args.time is False, the 'or' statement will assign time as 180.
#
# Beware: 
#   -o will return the same as -option, --option, and --o
#   this also means -o cannot be distinguished between --option and --other
#   remedy this by using more letters, -ot and -op will be distinguishable
# 
# Cheeky option checks.
# i.e:
#   if ['help', 'usage'] in args:
#       print 'show help'
# 
# or even:
#   if 'config' not in args:
#       print 'get mad'
# 
# 

import os, sys, re, ast

class EasyArgs:
    def __init__(self, args=sys.argv):
        self._noops = []
        self._ops = {}
        
        o = None
        for v in args:
            if v.startswith("-") and o is None:
                # found an option, next loop be the value
                o = v.replace("-", "")
            elif o is not None:
                if v.startswith("-"):
                    self._ops[o] = True # the option exists, but has no value
                    o = v.replace("-", "") # still load next option
                else:
                    self._ops[o] = self._converttype(v)
                    o = None # reset
            else:
                # when o is none, it is now an argument
                self._noops.append(self._converttype(v))
        
        # catch end options
        if o is not None:
            self._ops[o] = True
    
    # i.e: EasyArgs.option_name # => option_var
    def __getattr__(self, key):
        if key in self._ops:
            return self._ops[key]
        
        for op in self._ops:
            if key.startswith(op):
                return self._ops[op]
        
        return False
        
    # i.e: EasyArgs[0] # => first arg (typically script.py)
    def __getitem__(self, key):
        return self._noops[key]
    
    # number of args
    def __len__(self):
        return len(self._noops)
    
    # iterator of args i.e: for i in args
    def __iter__(self):
        return self._noops.__iter__()
    
    # test for available options
    def __contains__(self, key):
        # test lists - i.e: ['version', 'usage'] in EasyArgs
        if type(key) is list:
            for o in key:
                if self.__getattr__(o) is False:
                    self._missing = o
                    return False
            # else
            return True
        # test regular keys - i.e: 'config' in EasyArgs
        else:
            return (key in self._ops)
    
    # An inner routine function to auto-convert type from strings
    def _converttype(self, var):
        # test float
        if "." in var:
            try: return float(var)
            except: pass
        
        # test int
        try: return int(var)
        except: pass
        
        # test bool
        if var in ["True", "False"]:
            return var == "True"
        
        # test tuple, lists
        if re.match("[\(\[].*[\)\]]", var) is not None:
            return ast.literal_eval(var)
        
        return var
    
    # string representation - i.e: print EasyArgs()
    def __str__(self):
        out = []
        for a in self._noops: out.append(str(a))
        for o in self._ops: out.append("{}:{}".format(o, self._ops[o]))
        return ", ".join(out)
        
    
if __name__ == "__main__" and sys.argv[1] == 'test':
    test_args = ["-u", "element 2", "regular", "--special", "variable1", \
                 "-he", "world", "nothing", "--true", "-ha", "again", \
                 "-tuple", "(9,6)", "-list", "[1,4,55,\"seven\"]", "--end"]
    args = EasyArgs(test_args)
    
    print "testing:", test_args
    print ""
    print "verify len (2):", len(args) >= 2
    print "verify opts [special, u, hello]:", ["special", "u", "hello"] in args
    print "verify opts - bad:", "bad" in args
    print ""
    print "empty:", args.empty
    print "u:", args.u
    print "0:", args[0]
    print "1:", args[1]
    print "s:", args.s
    print "hello:", args.hello
    print "haha:", args.haha
    print "tuple:", args.tuple, type(args.tuple)
    print "list:", args.list, type(args.list)
    print ""
    print "args:", [i for i in args], "size:", len(args)
    print ""
    print "all:", args
    