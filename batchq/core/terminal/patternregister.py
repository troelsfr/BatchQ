import re
import inspect
def convert_to_int(x):
    try:
        return int(x)
    except:
        return x

class PatternRegister(object):
    """
    This objects is a register for mapping keystrokes into functions. A
    keystroke is added using the register method and the function is
    retrieved using get_function.
    """
    def __init__(self):
        self._function_register = {}
        self._regex_register = {}
        self._fullregex = ""
        self._first = True
        self._search_pattern = None

    def register(self,*kwds, **kwargs):
        """
        Registers a new keystroke.
        """
        verbose = True
        if 'verbose' in kwargs:
            verbose = kwargs['verbose']

        def decorate(f):
            def decorator(*args, **kwargs):
#                print "Hello world", f.__name__
                #                pass
                #                if verbose:
                print "Invoking ", f.__name__, f, args, kwargs
                return f(*args, **kwargs)
                #                print "Pattern for ", f.__name__, newf


            i =0
#            print "Decorating ", f.__name__
            for k in kwds:
                key = "%s_%d" %( f.__name__, i)
                self._function_register[key] = decorator
                self._regex_register[key] = k.replace(r"(?P<", "(?P<%s_"%key)
                if self._first:
                    self._fullregex += "(?P<%s>%s)"%(key,self._regex_register[key])
                    self._first = False
                else:
                    self._fullregex += "|(?P<%s>%s)"%(key,self._regex_register[key])

                self._search_pattern = re.compile(self._fullregex)
                i+=1

            return decorator
        return decorate



    @property
    def re(self):
        """
        This property holds a regex pattern for identifying
        keystrokes. The pattern is naive made, and thus, can easily be
        optimised. However, the function is provided to enable fast
        development. 
        """
        return self._search_pattern

    def get_function(self, k):
        """
        Given a keystroke combination k, this function returns the
        registered function. It returns None if no function is found.
        """
        if k in self._function_register:
            return self._function_register[k]
        return None



class ReductionRegister(object):
    def __init__(self):
        self._inside_pattern = False
        self.pattern_start = {u'\x00':'NUL', u'\x01':'SOH',u'\x02':'STX',u'\x03':'ETX',u'\x04':'EOT',u'\x05':'ENQ',u'\x06':'ACK',u'\x07':'BEL',
                              u'\x08':'BS',u'\x09':'TAB',u'\x0A':'NL',u'\x0B':'VT',u'\x0C':'NP',u'\x0D':'CR',u'\x0E':'SO',u'\x0F':'SI',u'\x10':'DLF',
                              u'\x11':'DC1',u'\x12':'DC2',u'\x13':'DC3',u'\x14':'DC4',u'\x15':'NAK',u'\x16':'SYN',u'\x17':'ETB',u'\x18':'CAN',u'\x19':'EM',
                              u'\x1A':'SUB',u'\x1b': 'ESC',u'\x1C':'FS',u'\x1D':'GS',u'\x1E':'RS',u'\x1F':'US'}
        self.basic_reductions = {'ESC [': 'CSI', 'ESC D': 'IND', 'ESC E': 'NEL', 'ESC H': 'HTS', 'ESC M': 'RI', 'ESC N': 'SS2','ESC O': 'SS3',
                  'ESC P': 'DCS', 'ESC V': 'SPA', 'ESC W':'EPA', 'ESC X': 'SOS', 'ESC Z':'CSI c', "ESC \\": 'ST', 'ESC ]':'OSC',
                  'ESC ^': 'PM', 'ESC _':'APC'}
        self.reductions = { '0':'','1':'','2':'','3':'','4':'','5':'','6':'','7':'','8':'','9':'', ";":""}
        self.reductions.update(self.basic_reductions)

        self._cur_full_pattern = ""
        self._own = None


# Characters and reductions
 # "ESC D", "ESC E", "ESC H", "ESC M", "ESC N", "ESC O", "ESC P", "ESC V", "ESC W", "ESC X", "ESC Z", "ESC [", "ESC \\", "ESC ]", "ESC ^", "ESC _", "BEL", "BS", "CR", "ENQ", "FF", "LF", "SI", "SO", "SP", "TAB", "VT", 
        self.rules = {}
        self.defaults = {}
        self._cur_pattern = ""
        self._cur_reduced_pattern = ""
        self.pattern_end = ["ESC SP F", "ESC SP G", "ESC SP L", "ESC SP M", "ESC SP N", "ESC # 3", 
                            "ESC # 4", "ESC # 5", "ESC # 6", "ESC # 8", "ESC % @", "ESC % G", "ESC ( Ch", "ESC ) Ch", 
                            "ESC * Ch", "ESC + Ch", "ESC - Ch", "ESC . Ch", "ESC / Ch", "ESC 6", "ESC 7", "ESC 8", "ESC 9", 
                            "ESC =", "ESC >", "ESC F", "ESC c", "ESC l", "ESC m", "ESC n", "ESC o", "ESC |", "ESC }", "ESC ~", 
                            "APC Pt ST", "DCS Ps ; Ps | Pt ST", "DCS $ q Pt ST", "DCS + p Pt ST", "DCS + q Pt ST", "CSI Ps @", 
                            "CSI Ps A", "CSI Ps B", "CSI Ps C", "CSI Ps D", "CSI Ps E", "CSI Ps F", "CSI Ps G", "CSI Ps ; Ps H", 
                            "CSI Ps I", "CSI Ps J", "CSI ? Ps J", "CSI Ps K", "CSI ? Ps K", "CSI Ps L", "CSI Ps M", "CSI Ps P", 
                            "CSI Ps S", "CSI Ps T", "CSI Ps ; Ps ; Ps ; Ps ; Ps T", "CSI > Ps ; Ps T", "CSI Ps X", "CSI Ps Z", "CSI Pm `", "CSI Ps b", 
                            "CSI Ps c", "CSI > Ps c", "CSI Pm d", "CSI Ps ; Ps f", "CSI Ps g", "CSI Pm h", "CSI ? Pm h", "CSI Pm i", 
                            "CSI ? Pm i", "CSI Pm l", "CSI ? Pm l", "CSI Pm m", "CSI > Ps ; Ps m", "CSI Ps n", "CSI > Ps n", 
                            "CSI ? Ps n", "CSI > Ps p", "CSI ! p", "CSI Ps $ p", "CSI ? Ps $ p", "CSI Ps ; Ps \" p", 
                            "CSI Ps q", "CSI Ps SP q", "CSI Ps \" q", "CSI Ps ; Ps r", "CSI ? Pm r", "CSI Pt ; P l", 
                            "CSI s", "CSI ? Pm s", "CSI Ps ; Ps ; Ps t", "CSI Pt ; Pl ; Pb ; Pr ; Ps $ t", "CSI > Ps ; Ps t", "CSI Ps SP t", 
                            "CSI u", "CSI Ps SP u", "CSI Pt ; Pl ; Pb ; Pr ; Pp ; Pt ; Pl ; Pp $ v", "CSI Pt ; Pl ; Pb ; Pr ' w", 
                            "CSI Ps x", "CSI Ps x", "CSI P c ; Pt ; P l ; P b ; P r $ x", "CSI Ps ; Pu ' z", 
                            "CSI Pt ; Pl ; Pb ; Pr $ z", "CSI Pm ' {", "CSI Pt ; P l ; P b ; P r $ {", "CSI Ps ' |", 
                            "CSI Pm SP }", "CSI Pm SP ~", "OSC Ps ; Pt ST", "OSC Ps ; Pt BEL", "PM Pt ST", "BEL", "BS", "TAB", "LF", "VT", "FF", 
                            "CR"]
# Tektronix 4014 Mode
# [ "ESC ETX", "ESC ENQ", "ESC FF", "ESC SO", "ESC SI", "ESC ETB", "ESC CAN", "ESC SUB", "ESC FS", "ESC 8", "ESC 9", 
#                            "ESC :", "ESC ;", "OSC Ps ; P", "ESC `", "ESC a", "ESC b", "ESC c", "ESC d", "ESC h", "ESC i", "ESC j", "ESC k", "ESC l", 
#                            "ESC p", "ESC q", "ESC r", "ESC s", "ESC t", "FS", "GS", "RS", "US", "ESC A", "ESC B", "ESC C", "ESC D", 
#                            "ESC F", "ESC G", "ESC H", "ESC I", "ESC J", "ESC K", "ESC Y Ps P", "ESC Z", "ESC =", "ESC >", "ESC <"]

        self._allowed_characters = ["0","A", "B","4", "C","5","R","Q","K","Y","E","Z","H","7","="]
        self.intermediate_stage = ["ESC #", "ESC %", "ESC (", "ESC )"]

        for a in self.pattern_start.itervalues():
            if a != "ESC" and not a in self.pattern_end: self.pattern_end.append(a)

        self.patterns = {}
        for a in self.pattern_end:
            if ";" in a:
                self.patterns[a] = [a]
            key = a.replace("Ps ","").replace("Pt ","").replace("Pm ","").replace("; ","")
            if "Ch" in key:
                for c in self._allowed_characters:
                    nkey = key.replace("Ch", c)
                    if key in self.patterns:
                        self.patterns[nkey].append(a)
                    else:
                        self.patterns[nkey] = [a]
            elif key in self.patterns:
                self.patterns[key].append(a)
            else:
                self.patterns[key] = [a]


        self._last_was_command = False

    def parse(self, char):
        if not self._inside_pattern:
            if char in self.pattern_start:

                self._cur_pattern = "" 
                self._cur_reduced_pattern = "" 
                self._cur_parameters = [""]
                self._inside_pattern = True
            else: return self._inside_pattern

#        if len(self._cur_reduced_pattern) > 200:
#            print "This seems wrong:", 
#            print "PATTERN", self._cur_pattern
#            print "RPATTERN", self._cur_reduced_pattern
#            exit(0)

        if char in self.pattern_start:
            add = " "
            if self._cur_reduced_pattern == "":
                add = ""
            self._cur_reduced_pattern += add + self.pattern_start[char]
            self._cur_pattern += add + self.pattern_start[char]
            self._last_was_command = True
        else:
            if char == ";": self._cur_parameters.append("")                
            self._cur_reduced_pattern += " " + char
            self._cur_pattern += " " + char
            self._last_was_command = False

        for i, o  in self.basic_reductions.iteritems():
            n = len(i)
            while self._cur_pattern[-n:] == i:
                self._cur_pattern = self._cur_pattern[:-n]+o
                self._cur_reduced_pattern = self._cur_reduced_pattern[:-n]+o
                self._last_was_command = True

        if (self._cur_pattern in self.patterns or self._cur_reduced_pattern in self.patterns
            or self._cur_reduced_pattern in self.intermediate_stage):
            self._last_was_command = True


        if not self._last_was_command: 
            if char !=";": self._cur_parameters[-1] += char
            self._cur_reduced_pattern = self._cur_reduced_pattern[:-2]

        if  self._cur_reduced_pattern in self.patterns:
            self._inside_pattern = False
#            print "FOUND PATTERN", self._cur_pattern, " with ", self._cur_parameters, "(",self._cur_reduced_pattern,")"
            pattern = self.patterns[self._cur_reduced_pattern][0]
#            print pattern
          
            if pattern in self.rules or "__catch_all__" in self.rules:
                f = self.rules[pattern] if pattern in self.rules else self.rules["__catch_all__"]
#                print "Function",f 

                args =[self._cur_pattern,] 
                defargs = self.defaults[self._cur_pattern] if self._cur_pattern in self.defaults else ()
                
                while len(self._cur_parameters)>0 and self._cur_parameters[-1] == "": self._cur_parameters.pop()
                
                for i in range(0, max( len(defargs), len(self._cur_parameters) )):
                    a = self._cur_parameters[i] if i < len(self._cur_parameters) else defargs[i]
                    if a == "" and i < len(defargs):
                        a = defargs[i]
                    a = convert_to_int(a)
                    args.append(a)

                
                f(self._own,*args)
            return pattern

        return self._inside_pattern


    def set_owner(self, own):
        self._own = own

    def reencode(self, pat):
        return pat.replace("?",r"\?")

    def hook(self, *pattern, **kwargs):       
        def decorate(f):            
            defaults = kwargs['defaults'] if 'defaults' in kwargs else ()
            for p in pattern:                                   
                self.rules[p] = f
                self.defaults[p] = defaults
            return f
        return decorate
