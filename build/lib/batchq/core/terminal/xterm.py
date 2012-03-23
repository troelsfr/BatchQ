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

# Implement XTerm from http://invisible-island.net/xterm/ctlseqs/ctlseqs.html
# http://publib.boulder.ibm.com/infocenter/aix/v6r1/index.jsp?topic=%2Fcom.ibm.aix.cmds%2Fdoc%2Faixcmds1%2Faixterm.htm
# http://www.google.ch/url?sa=t&rct=j&q=&esrc=s&source=web&cd=4&cts=1331737438612&ved=0CEkQFjAD&url=http%3A%2F%2Fwww.kitebird.com%2Fcsh-tcsh-book%2Fctlseqs.ps&ei=6LJgT7nQFIihOq2o8IMI&usg=AFQjCNHRPxw71Ux5uPgSc746Ma-l6S1jmA&sig2=20VWUr9AVh4LkqlJZjxbPwa
# http://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes
# http://www.asciitable.com/

from batchq.core.terminal.patternregister import PatternRegister,ReductionRegister
from batchq.core.terminal.base import BaseInterpreter

XTermEscapeRegister = PatternRegister()
XTermKeyRegister = PatternRegister()

XTermRegister = ReductionRegister()
import copy

def convert_to_int(x):
    try:
        return int(x)
    except:
        return x

class XTermInterpreter(BaseInterpreter):
    def __init__(self):
        super(XTermInterpreter, self).__init__(XTermEscapeRegister, XTermKeyRegister,copy.deepcopy(XTermRegister))


###################
### KEYS

    @XTermRegister.hook("NUL")
    def null(self,sequence):
        pass


    @XTermRegister.hook("SOH")
    def start_of_heading(self,sequence):
        pass

    @XTermRegister.hook("STX")
    def start_of_text(self,sequence):
        pass

    @XTermRegister.hook("ETX")
    def end_of_text(self,sequence):
        pass

#
    @XTermRegister.hook("EOT")
    def end_of_transmission(self,sequence):
        pass

    @XTermRegister.hook("ENQ")
    def enquiry(self,sequence):
        pass

    @XTermRegister.hook("ACK")
    def acknowledge(self,sequence):
        pass

    @XTermRegister.hook("BEL")
    def bell(self,sequence):
        print "RING RING RING ---- "*4



    @XTermRegister.hook("BS")
    def backspace(self,sequence):
        self.cursor_back()


    @XTermRegister.hook("TAB")
    def horisontal_tab(self,sequence):
        #        self.put("\t")
        self._curchar += 8

    @XTermRegister.hook("NL")
    def newline(self,sequence):
        self._curline+=1
        self.fix_buffer()

    @XTermRegister.hook("VT")
    def vertical_tab(self,sequence):
        self._curline += 8
        

    @XTermRegister.hook("NP")
    def newpage(self,sequence):
        self._curline+=1
        self.fix_buffer()


    @XTermRegister.hook("CR")
    def carriage_return(self,sequence):
#        print "Hello world"
#        print ord(self._full_echo[-4]),ord(self._full_echo[-3]),ord(self._full_echo[-2]),ord(self._full_echo[-1])
#        print "Hello world"
        self._curchar = 0
        self.fix_buffer()

    @XTermRegister.hook("SO")
    def shift_out(self,sequence):
        pass

    @XTermRegister.hook("SI")
    def shift_in(self,sequence):
        pass

# TODO: MISSING MISSING MISSING
#                              'CR',u'\x0E':'SO',u'\x0F':'SI',u'\x10':'DLF',
#                              u'\x11':'DC1',u'\x12':'DC2',u'\x13':'DC3',u'\x14':'DC4',u'\x15':'NAK',u'\x16':'SYN',u'\x17':'ETB',u'\x18':'CAN',u'\x19':'EM',
#                              u'\x1A':'SUB',u'\x1b': 'ESC',u'\x1C':'FS',u'\x1D':'GS',u'\x1E':'RS',u'\x1F':'US'}


    @XTermRegister.hook("__catch_all__")
    def warning_non_supported (self,sequence, *args): # <ESC>[? ... h or <ESC>[? ... m or <ESC>[? ...l
        print "WARNING: No support for sequence ",sequence
###############
## Escape sequences
    @XTermEscapeRegister.register(r"\x1b\[(?P<quest>\??)(?P<attributes>(\d+;)*\d*)(?P<property>(h|l|m))")
    def set_mode_old (self,quest= None, attributes = None, property = None): # <ESC>[? ... h or <ESC>[? ... m or <ESC>[? ...l
        pass
#,r"CSI \?(?P<Pm1>(?:\d+;)*\d*)?h")

    @XTermRegister.hook("CSI ? Pm h","CSI Pm h", "CSI ? Pm l","CSI Pm l","CSI ? Pm m","CSI Pm m")
    def set_mode (self,sequence, *args): # <ESC>[? ... h or <ESC>[? ... m or <ESC>[? ...l
        pass


    @XTermRegister.hook("ESC >")
    def set_numeric_keypad_mode (self, seq): # <ESC>>
        pass



    @XTermRegister.hook("ESC =")
    def set_alternate_keypad_mode (self, seq): 
        pass



    @XTermRegister.hook("ESC ( A","ESC ( B", "ESC ( 0", "ESC ( 1", "ESC ( 2","ESC ) A","ESC ) B", "ESC ) 0", "ESC ) 1", "ESC ) 2")
    def set_character_set (self, seq): 
        pass


    @XTermRegister.hook("ESC N")
    def set_single_shift2 (self, seq): 
        pass


    @XTermRegister.hook("ESC O")
    def set_single_shift3 (self, seq): 
        pass



    @XTermRegister.hook("CSI Ps ; Ps r")
    def set_scrolling_free_region (self, seq = "", line1 = 1, line2= 80):
        self._topline = line1 - 1
        self._bottomline = line2 - 1
        self.fix_buffer()

    @XTermRegister.hook("CSI Ps A", defaults = (1,) )
    def cursor_up (self,seq="",count=1):
        self._curline -= count
        if self._curline < 0: self._curline = 0

    @XTermRegister.hook("CSI Ps B", defaults = (1,) )
    def cursor_down (self,seq="",count=1):
        self._curline += count
        n = len(self._lines)
        if self._curline > n: self._lines += [""]*(self._curline - n)

    @XTermRegister.hook("CSI Ps C", defaults = (1,) )
    def cursor_forward (self,seq="",count=1):
        self._curchar += count
        n = len(self._lines[self._curline])
        if self._curchar>n: self._lines[self._curline] += " "*(self._curchar - n)

    @XTermRegister.hook("CSI Ps D", defaults = (1,) )
    def cursor_back (self,seq="",count=1):
        self._curchar -= count
        if self._curchar<0: self._curchar = 0


    @XTermRegister.hook("CSI Ps ; Ps H", defaults = (1,1) )
    def cursor_home (self, seq = "", line=1, char=1):
        self._curline = line - 1 
        self._curchar = char - 1
        self.fix_buffer()

    @XTermRegister.hook("CSI Ps ; Ps f", defaults = (1,1) )
    def cursor_force_position (self, seq = "", line=1, char=1): 
        self._curline = line - 1
        self._curchar = char - 1
        self.fix_buffer()


    @XTermRegister.hook("CSI 7")
    def cursor_save_attrs (self, seq = ""): # 
        self._home_line = self._curline
        self._home_char = self._curchar
        self._home_attributes = self._attributes



    @XTermRegister.hook("ESC 8")
    def cursor_restore_attrs (self, seq =""): # <ESC>8 
        self._curline = self._home_line
        self._curchar = self._home_char
        self._attributes = self._home_attributes
        self.fix_buffer()



    @XTermRegister.hook("ESC H")
    def set_tab (self,seq = ""): # <ESC>H
        pass


    @XTermRegister.hook("CSI Ps g")
    def clear_tabs (self,seq = ""):
        pass


    @XTermRegister.hook("ESC # 3")
    def double_letters_height_top_half (self,seq = ""): # <ESC>#3
        pass

    @XTermRegister.hook("ESC # 4")
    def double_letters_height_bottom_half (self,seq = ""): # <ESC>#4
        pass

    @XTermRegister.hook("ESC # 5")
    def single_width (self,seq = ""): # <ESC>#5
        pass

    @XTermRegister.hook("ESC # 6")
    def double_width (self,seq = ""): # <ESC>#6
        pass

    @XTermRegister.hook("ESC # 8")
    def screen_alignment_display (self,seq = ""): # <ESC>#8
        pass


    @XTermRegister.hook("CSI Ps K",defaults = (0, ) )
    def erase_until (self,seq = "", k = 0): 
        if isinstance(k,str) and k[0] == "?": pass # TODO: Handle quenstion marks
        if k == 0:
            line = self._lines[self._curline]
            line = line[0:self._curchar]
            self._lines[self._curline] = line

        elif k == 1:
            line = self._lines[self._curline]
            line = line[self._curchar+1:len(line)]
            self._lines[self._curline] = line
        elif k == 2:
            self._lines[self._curline] = ""


    @XTermRegister.hook("CSI Ps J",defaults = (0, ) )
    def erase_display (self,seq = "", p = 0):
        if isinstance(p,str) and k[0] == "?": pass # TODO: Handle quenstion marks
        if p == 0:
            n = len(self._lines)
            self._lines = self._lines[0:self._curline]                       
        elif p==1:
            n = len(self._lines)
            self._lines = self._lines[self._curline+1:n]           
        elif p == 2:
            self._lines = [""]
            self._curchar = 0
            self._curline = 0
            self.fix_buffer()
        elif p == 3:
            print "TODO: feature not implemented"

    @XTermRegister.hook("CSI Ps G", defaults = (1,))
    def move_to_column (self, seq, n): 

        self._curchar = n - 1
        self.fix_buffer()

    @XTermRegister.hook("CSI Pm d", defaults = (1,))
    def move_to_row (self, seq, n): 
        self._curline = n - 1
        self.fix_buffer()


    @XTermRegister.hook("OSC Ps ; Pt BEL","OSC Ps ; Pt ST", defaults = (0,"XTerm"))
    def set_terminal_properties (self, seq,mode, *texts): 
        text = "".join(texts)
        

