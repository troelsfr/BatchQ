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

# Note the VT100 intepreter is still incomplete. Please consult 
# http://ascii-table.com/ansi-escape-sequences-vt-100.php for missing codes.
import re

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

    def register(self,*kwds):
        """
        Registers a new keystroke.
        """
        def decorate(f):
            i =0
            for k in kwds:
                key = "%s_%d" %( f.__name__, i)
                self._function_register[key] = f
                self._regex_register[key] = k.replace(r"(?P<", "(?P<%s_"%key)
                if self._first:
                    self._fullregex += "(?P<%s>%s)"%(key,self._regex_register[key])
                    self._first = False
                else:
                    self._fullregex += "|(?P<%s>%s)"%(key,self._regex_register[key])

                self._search_pattern = re.compile(self._fullregex)
                i+=1
            return f
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

VT100Register = PatternRegister()
KeyRegister = PatternRegister()

def convert_to_int(x):
    try:
        return int(x)
    except:
        return x

class VT100Interpreter(object):
    """
    This object implements VT100 interpretation.
    """
    def __init__(self):
        self.erase_screen()
        self._buffer = ""
        self._escpat = False
        self._VT100patterns = VT100Register.re
        self._KeyPatterns = KeyRegister.re
        self._last_monitor_char = 0
        self._last_monitor_line = 0
        self._mark_line = 0
        self._mark_char = 0
        self._full_echo = ""
        self._mark_echo = 0
        self._last_monitor_echo = 0
        self._echo_position = 0


        self._last_ret = ""

    def move_monitor_cursors(self):
        self._last_monitor_echo = self._echo_position
        self._last_monitor_char = self._curchar
        self._last_monitor_line = self._curline


    @property
    def monitor_echo(self):
        ret = self._full_echo[self._last_monitor_echo:self._echo_position]
        self._last_monitor_echo = self._echo_position
        return ret
    
    @property
    def escape_mode(self):
        return self._escpat

    @property
    def monitor(self):

        if self._curline < self._last_monitor_line: 
            return ""
        if self._curline == self._last_monitor_line and self._curchar < self._last_monitor_char: 
            return ""

        n = len(self._lines)
        buf = "\r\n".join(self._lines[self._last_monitor_line:(self._curline+1)])
        lenlastl = len(self._lines[self._curline])
        n = len(buf) - lenlastl + self._curchar
        ret = buf[self._last_monitor_char:n]

        self._last_monitor_char = self._curchar
        self._last_monitor_line = self._curline

        return ret
        
    @property
    def buffer(self):
        return "\n".join(self._lines)

    @property
    def last_escape(self):
        ret = ""
        n = len(self._full_echo)
        i = n-1
        while  i>=0 and self._full_echo[i] != u"\x1b":
            i-=1

        if i>=0:
            i+=1
#            print i
#            print self._full_echo[i:]
            ret ="<ESC>"
            ret+=self._full_echo[i:]
        return ret


    @property
    def echo(self):
        return self._full_echo

    @property
    def readable_echo(self):
        return self._full_echo.replace(u"\x1b", "<ESC>").replace(u"\x07", "<BEL>").replace(u"\x0D", "<RET>")


    def write(self, str):
        for c in str:
            self.writeChar(c)

    def writeChar(self,c):

        self._full_echo += c
        self._echo_position += 1

        if ord(c) == 27:
            self._escpat = True
            self._buffer = ""


        self._buffer+= c
        keym = self._KeyPatterns.search(c)
#        star = lambda x: str(ord(x))+"*" if self._escpat else x
#        print star(c),
        if self._escpat:
            m = self._VT100patterns.search(self._buffer)
            if m:
                f = lambda (x,y): True if y else False
                found = dict(filter(f, m.groupdict().iteritems()))
                kelem = ""
                lastlen = 1000000
                for k in found:
                    if len(k)< lastlen:
                        kelem = k
                        lastlen = len(k)
                del found[kelem]
                fnc = VT100Register.get_function(kelem) 
                kelem+="_"
                g = lambda x: x.replace(kelem,"")
                args = dict([(g(x),convert_to_int(y)) for (x,y) in  found.iteritems()])                
                
                fnc(self,**args)
                self._escpat = False

#                print kelem, args
        elif keym:            
            f = lambda (x,y): True if y else False
            found = dict(filter(f, keym.groupdict().iteritems()))
            kelem = ""
            lastlen = 1000000
            for k in found:
                if len(k)< lastlen:
                    kelem = k
                    lastlen = len(k)
            del found[kelem]
            fnc = KeyRegister.get_function(kelem) 
            kelem+="_"
            g = lambda x: x.replace(kelem,"")
            args = dict([(g(x),convert_to_int(y)) for (x,y) in  found.iteritems()])                        
            fnc(self,**args)            
        else:
            self.put(c)


    def set_mark(self):
        self._mark_line = self._curline
        self._mark_char = self._curchar
        self._mark_echo = self._echo_position

    def copy(self):
#        if self._curline < self._last_monitor_line: return ""
#        if self._curline == self._last_monitor_line and self._curchar < self._last_monitor_char: return ""

        n = len(self._lines)
        buf = "\n".join(self._lines[self._mark_line:n])
        n = len(buf)
        return buf[self._mark_char:n]

    def copy_echo(self):
        return self._full_echo[self._mark_echo:self._echo_position]


    def fix_buffer(self):
        n = len(self._lines)
        if self._curline+1 > n: self._lines += [""]*(self._curline - n + 1)
        if self._curline < 0: self._curline = 0
#        print self._curline, len(self._lines)
        n = len(self._lines[self._curline])
        if self._curchar<0: self._curchar = 0
        if self._curchar>n: self._lines[self._curline] += " "*(self._curchar - n + 1)


    def put(self,c):
        n = self._curchar
        m = len(self._lines[self._curline])
        self._lines[self._curline] = self._lines[self._curline][0:n] + c + self._lines[self._curline][n+1:m]
#        print self._curchar, self._lines
        self._curchar+=1
        self.fix_buffer()




    @KeyRegister.register(r"\n")
    def newline(self):
#        print "Making newline"
        self._curline+=1
#        self._curchar = 0
        self.fix_buffer()

    @KeyRegister.register(r"\r")
    def linestart(self):
        self._curchar = 0
        self.fix_buffer()


#    @KeyRegister.register(r"\n")
    def delete(self):
        self._curline+=1
        self._curchar = 0
        self.fix_buffer()



    @VT100Register.register(r"\x1b\[(?P<line>\d+);(?P<char>\d+)H")
    def cursor_home (self, line=1, char=1):
        self._curline = line
        self._curchar = char


    @VT100Register.register(r"\x1b\[(?P<count>\d+)D")
    def cursor_back (self,count=1): # <ESC>[{COUNT}D (not confused with down)
        self._curchar -= count
        if self._curchar<0: self._curchar = 0

    @VT100Register.register(r"\x1b\[(?P<count>\d+)B")
    def cursor_down (self,count=1): # <ESC>[{COUNT}B (not confused with back)
        self._curline += count
        n = len(self._lines)
        if self._curline > n: self._lines += [""]*(self._curline - n)
#        if self._curline > n: self._curline = n

    @VT100Register.register(r"\x1b\[(?P<count>\d+)C")
    def cursor_forward (self,count=1): # <ESC>[{COUNT}C
        self._curchar += count
        n = len(self._lines[self._curline])
        if self._curchar>n: self._lines[self._curline] += " "*(self._curchar - n)

    @VT100Register.register(r"\x1b\[(?P<count>\d+)A", r"M")
    def cursor_up (self,count=1): # <ESC>[{COUNT}A or <ESC> M 
        self._curline -= count
        if self._curline < 0: self._curline = 0

    @VT100Register.register(r"\x1b\[(?P<line>\d+);(?P<char>\d+)f")
    def cursor_force_position (self, line, char): # <ESC>[{ROW};{COLUMN}f
        self._curline = line
        self._curchar = char

    @VT100Register.register(r"\x1b7",r"\[s")
    def cursor_save_attrs (self): # <ESC>7 or <ESC>[s
        self._home_line = self._curline
        self._home_char = self._curchar

    @VT100Register.register(r"\x1b8",r"\[u")
    def cursor_restore_attrs (self): # <ESC>8 or <ESC>[u
        self._curline = self._home_line
        self._curchar = self._home_char

    @VT100Register.register(r"\x1b\[0?K")
    def erase_end_of_line (self): # <ESC>[0K -or- <ESC>[K

        line = self._lines[self._curline]
        line = line[0:self._curchar]
        self._lines[self._curline] = line

    @VT100Register.register(r"\x1b\[1K")
    def erase_start_of_line (self): # <ESC>[1K

        line = self._lines[self._curline]
        line = line[self._curchar+1:len(line)]
        self._lines[self._curline] = line

    @VT100Register.register(r"\x1b\[2K")
    def erase_line (self): # <ESC>[2K

        self._lines[self._curline+1] = ""

    @VT100Register.register(r"\x1b\[0?J")
    def erase_down (self): # <ESC>[0J -or- <ESC>[J
        n = len(self._lines)
        self._lines = self._lines[0:self._curline]           

    @VT100Register.register(r"\x1b\[1J")
    def erase_up (self): # <ESC>[1J
        n = len(self._lines)
        self._lines = self._lines[self._curline+1:n]           

    @VT100Register.register(r"\x1b\[2J")
    def erase_screen (self): # <ESC>[2J
        self._lines = [""]
        self._curchar = 0
        self._curline = 0


    @VT100Register.register(r"\x1b\(")
    def set_default_font (self):
        pass

    @VT100Register.register(r"\x1b\)")
    def set_alt_font (self):
        pass

    @VT100Register.register(r"\x1b\[(?P<attributes>(\d+;)*\d+)m")
    def set_display_attr (self,attributes):
        pass
#        print "XXXXXXXX::: Setting display attr", attributes




    @VT100Register.register(r"\x1b\[\?(?P<mode>\d*)(?P<property>(h|l|m))")
    def set_mode (self,mode, property): # <ESC>[? ... h or <ESC>[? ... m or <ESC>[? ...l
        pass

    @VT100Register.register(r"(\x1b)c")
    def reset_device (self): # <ESC>c
        pass

    @VT100Register.register(r"\x1b\[7h")
    def enable_line_wrap (self): # <ESC>[7h
        pass

    @VT100Register.register(r"\x1b\[7l")
    def disable_line_wrap (self): # <ESC>[7l
        pass

    @VT100Register.register(r"\x1b\]0;.*\x07")
    def unknown1 (self): # <ESC>]0;
        pass



                      
    def set_tab (self): # <ESC>H
        pass

    def clear_tab (self): # <ESC>[g
        pass

    def clear_all_tabs (self): # <ESC>[3g
        pass


    def scroll_constrain (self):
        # This is not possible 
        pass


    def scroll_screen (self): # <ESC>[r
        # This is not possible 
        pass

    def scroll_screen_rows (self, rs, re): # <ESC>[{start};{end}r
        # This is not possible 
        pass


    def scroll_down (self): # <ESC>D
        # This is not possible 
        pass

    def scroll_up (self): # <ESC>M
        # This is not possible 
        pass



if __name__ == "__main__":
    test = VT100Interpreter()
    test.write("Hello0\x1b[1D world\n!!!\x1b[2D\x1b[1A3");

