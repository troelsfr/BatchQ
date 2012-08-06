def convert_to_int(x):
    try:
        return int(x)
    except:
        return x
import copy


class BaseInterpreter(object):
    """
    This object implements the base interpretater.
    """
    def __init__(self,escape_register, key_register, pattern_reg = None,  max_cols = 80, max_rows = 240):
        self._max_buffer_size = 10000
        self._max_cols = max_cols
        self._max_rows = max_rows
        self._min_show = 80

        self._mark_line = 0
        self._mark_char = 0
        self._curline = 0
        self._curchar = 0
        self._last_monitor_char = 0
        self._last_monitor_line = 0

        self._escpat = False
        self._escape_patterns = escape_register.re
        self._KeyPatterns = key_register.re
        self._escape_register = escape_register
        self._key_register = key_register
        self._pattern_reg = pattern_reg
        self._full_echo = ""
        self._swap_full_echo = ""
        self._mark_echo = 0
        self._last_monitor_echo = 0
        self._echo_position = 0

        self._lines = []
        self._swapped_lines = []
        self._attributes = {}
        self._last_ret = ""
        self._home_line = 0
        self._home_char = 0
        self._home_attributes = {}
        self._debug = False
        self._carriage_return = 0

        self._reconstruct_copy = True
        self._buffer_copy = ""
        self._last_curline = 0
        self._last_curchar = 0
        self._escape_pattern = False

        if not pattern_reg is None: pattern_reg.set_owner(self)
        self.erase_lines()
        self.fix_buffer()
        
    Deprecated = 1
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
        buf = "\r\n".join([str(a) for a in self._lines[self._last_monitor_line:(self._curline+1)]])
        lenlastl = len(self._lines[self._curline])
        n = len(buf) - lenlastl + self._curchar
        ret = buf[self._last_monitor_char:n]

        self._last_monitor_char = self._curchar
        self._last_monitor_line = self._curline

        return ret
        
    @property
    def buffer(self):
        sl = ("\n".join(self._swapped_lines)).replace("\r\n","")
        if sl!="": sl+="\n"
        return  sl + ("\n".join([str(a).strip(" ") for a in self._lines])).replace("\r\n","")

    @property
    def reduced_buffer(self):
        return  ("\n".join([str(a) for a in self._lines])).replace("\r\n","")

    @property
    def last_escape(self):
        ret = ""
        n = len(self._full_echo)
        i = n-1
        while  i>=0 and self._full_echo[i] != u"\x1b":
            i-=1

        if i>=0:
            i+=1
            ret ="<ESC>"
            ret+=self._full_echo[i:]
        return ret


    def _make_readable(self, echo):
        pattern_start = {'\x00':'NUL', '\x01':'SOH','\x02':'STX','\x03':'ETX','\x04':'EOT','\x05':'ENQ','\x06':'ACK','\x07':'BEL',
                         '\x08':'BS','\x09':'TAB','\x0A':'NL','\x0B':'VT','\x0C':'NP','\x0D':'CR','\x0E':'SO','\x0F':'SI','\x10':'DLF',
                         '\x11':'DC1','\x12':'DC2','\x13':'DC3','\x14':'DC4','\x15':'NAK','\x16':'SYN','\x17':'ETB','\x18':'CAN','\x19':'EM',
                         '\x1A':'SUB','\x1b': 'ESC','\x1C':'FS','\x1D':'GS','\x1E':'RS','\x1F':'US'}
        basic_reductions = {'ESC [': 'CSI', 'ESC D': 'IND', 'ESC E': 'NEL', 'ESC H': 'HTS', 'ESC M': 'RI', 'ESC N': 'SS2','ESC O': 'SS3',
                            'ESC P': 'DCS', 'ESC V': 'SPA', 'ESC W':'EPA', 'ESC X': 'SOS', 'ESC Z':'CSI c', "ESC \\": 'ST', 'ESC ]':'OSC',
                            'ESC ^': 'PM', 'ESC _':'APC'}
        for a,b in pattern_start.iteritems():
            echo = echo.replace(a,b+" ")

        for a,b in basic_reductions.iteritems():
            echo = echo.replace(a,"<"+b+">")

        for a,b in pattern_start.iteritems():
            echo = echo.replace(b+" ","<"+b+">")
        
        return echo.replace("<NL>", "\n")

    @property
    def swapped_echo(self):
        return self._make_readable(self._swap_full_echo)

    @property
    def active_echo(self):
        return self._make_readable(self._full_echo)

    @property
    def echo(self):
        return self._swap_full_echo+self._full_echo

    @property
    def readable_echo(self):
        return self._make_readable(self.echo)


    def write(self, str):
        # str = u"%s"%str

        self._full_echo+=str
        self._echo_position += len(str)

        for c in str:
            self.writeChar(c,False)


    def writeChar(self,c, write_echo= True):
        if write_echo:
            self._full_echo += c
            self._echo_position += 1

        pat = self._pattern_reg.parse(c)
        if pat:
            self._escape_pattern = True
            if pat == "NL":
                self._buffer_copy += "\n"
            self.fix_buffer()
        else:
            if self._escape_pattern:
                d1 = self._curchar - self._last_curchar
                d2 = self._curline - self._last_curline
                if d2 == 0:
                    self._reconstruct_copy = d1 != 1
                elif d1 == 0:
                    self._reconstruct_copy = d2 != 1
                self._escape_pattern = False

            self._last_curchar = self._curchar 
            self._last_curline = self._curline

            self.put(c)

    @property
    def position(self):
        return self._curchar,self._curline

    def swap_out(self):

        if len(self._swapped_lines) > self._max_rows:
            # TODO: store linees to file
            self._swapped_lines = self._swapped_lines[-self._max_rows:]

        if self._mark_line == 0: return
        swap_until = self._mark_line
        self._swapped_lines += [str(a).strip(" ") for a in self._lines[0:swap_until]]
        del self._lines[0:swap_until]
        self._mark_line -= swap_until
        self._curline  -= swap_until
        self._last_monitor_line -= swap_until

        if self._last_monitor_echo > self._max_buffer_size:
            self._swap_full_echo = self._full_echo[:self._last_monitor_echo]
            self._full_echo = self._full_echo[self._last_monitor_echo:]
            self._echo_position -= self._last_monitor_echo
            self._mark_echo -=self._last_monitor_echo
            self._last_monitor_echo = 0

    def swap_in(self, line):
        # TODO: yet to be implemented
        pass

    def set_mark(self,line = None, char = None, echo = None):
        self._mark_line = self._curline
        if not line is None:
            self._mark_line += line
            self._reconstruct_copy = True

        self._mark_char = self._curchar
        if not char is None:
            self._mark_char += char
            self._reconstruct_copy = True

        self._mark_echo = self._echo_position
        if not echo is None:
            self._mark_echo -= echo
            self._reconstruct_copy = True

        self.swap_out()
        
#        print "RESETING BUFFER COPY"
        self._buffer_copy = ""

    def append_spaces(self, line, n=1):
        pass
#        self._lines[line] += " "*n

    def append_empty_lines(self, n=1):
        #        if self._min_show - self._curline < 0:
#        print "Appending ", n, self._curline, len(self._lines)
        #self.set_mark(-self._min_show,-self._curchar)
        ##### TODO: This is a major slow down if the output is large. Fix with constant buffer
        self._lines += [copy.deepcopy(a) for a in [bytearray([' ']*(self._max_cols+1))]*n]

    def erase_lines(self, f=None,t=None):
        if f is None and t is None:
            self._lines = [bytearray([' ']*(self._max_cols+1))]
        elif t is None:
            for i in range(f, self._max_cols+1):
                self._lines[i] = [bytearray([' ']*(self._max_cols+1))]
        else:
            for i in range(f, t):
                self._lines[i] = [bytearray([' ']*(self._max_cols+1))]


    def copy(self):

        if self._reconstruct_copy: 
            n = len(self._lines)
            m = len(self._lines[self._curline])
            self._reconstruct_copy = False
            self._buffer_copy = "\n".join([str(a).strip(" ") for a in self._lines[self._mark_line:n]]).replace(u"\r\n","")[self._mark_char:]

        return self._buffer_copy

    def copy_until_end(self,char, line):
        n = len(self._lines)
        ### TODO: Requires heavy optimisation

        buf = ("\n".join([str(a).strip(" ") for a in self._lines[line:n]])).replace("\r\n","")
        n = len(buf)
        return buf[char:n]



    def copy_echo(self):
        return self._full_echo[self._mark_echo:self._echo_position]


    def fix_buffer(self):
        n = len(self._lines)
        if self._curline+1 > n: self.append_empty_lines(self._curline - n + 1)
        if self._curline < 0: self._curline = 0

        if self._curchar<0: self._curchar = 0
        if self._curchar>self._max_cols: self._curchar = self._max_cols


    def put(self,c):
        self._buffer_copy += c
        if self._curchar >= self._max_cols:

            self._lines[self._curline][self._max_cols] = "\r" 
            # TODO: Only if wordwrap enabled
            self._curchar = 0
            self._curline +=1
            self.fix_buffer()


        self._lines[self._curline][self._curchar] = c

        self._curchar+=1
        self.fix_buffer()
