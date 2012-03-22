
def convert_to_int(x):
    try:
        return int(x)
    except:
        return x

class BaseInterpreter(object):
    """
    This object implements the base interpretater.
    """
    def __init__(self,escape_register, key_register, pattern_reg = None,  max_cols = 80, max_rows = 80):
        self.erase_display(p = 2)
        self._buffer = ""
        self._escpat = False
        self._escape_patterns = escape_register.re
        self._KeyPatterns = key_register.re
        self._escape_register = escape_register
        self._key_register = key_register
        self._pattern_reg = pattern_reg
        self._last_monitor_char = 0
        self._last_monitor_line = 0
        self._mark_line = 0
        self._mark_char = 0
        self._full_echo = ""
        self._mark_echo = 0
        self._last_monitor_echo = 0
        self._echo_position = 0
        self._curline = 0
        self._curchar = 0
        self._lines = []
        self._attributes = {}
        self._last_ret = ""
        self._home_line = 0
        self._home_char = 0
        self._home_attributes = {}
        self._debug = False
        if not pattern_reg is None: pattern_reg.set_owner(self)

        self.fix_buffer()
        

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
        self._buffer+= c

        if self._pattern_reg.parse(c):
            pass
        else:
            self.put(c)
#            print c, 

    @property
    def position(self):
        return self._curchar,self._curline

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

    def copy_until_end(self,char, line):
        n = len(self._lines)
        buf = "\n".join(self._lines[line:n])
        n = len(buf)
        return buf[char:n]



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
