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
# http://www.termsys.demon.co.uk/vtansi.htm

### TODO: Figure out what is meant by <ESC>[?0h ... <ESC>[1;2;0h ? <ESC>[120h

from batchq.core.terminal.patternregister import PatternRegister
from batchq.core.terminal.base import BaseInterpreter

VT100Register = PatternRegister()
KeyRegister = PatternRegister()

class VT100Interpreter(BaseInterpreter):
    """
    This object implements VT100 interpretation.
    """
    def __init__(self):
        super(VT100Interpreter, self).__init__(VT100Register, KeyRegister)
###################
### KEYS
    @KeyRegister.register(r"\x00")
    def null(self):
        pass

    @KeyRegister.register(r"\x01")
    def start_of_heading(self):
        pass

    @KeyRegister.register(r"\x02")
    def start_of_text(self):
        pass

    @KeyRegister.register(r"\x03")
    def end_of_text(self):
        pass

    @KeyRegister.register(r"\x04")
    def end_of_transmission(self):
        pass

    @KeyRegister.register(r"\x05")
    def enquiry(self):
        pass

    @KeyRegister.register(r"\x06")
    def acknowledge(self):
        pass


    @KeyRegister.register(r"\x07")
    def bell(self):
        pass

    @KeyRegister.register(r"\x08")
    def backspace(self):
        self.cursor_back()

    @KeyRegister.register(r"\x09")
    def horisontal_tab(self):
        self.put("\t")

    @KeyRegister.register(r"\x0A")
    def newline(self):
        self._curline+=1
        self.fix_buffer()

    @KeyRegister.register(r"\x0B")
    def vertical_tab(self):
        pass

    @KeyRegister.register(r"\x0C")
    def newpage(self):
        self._curline+=1
        self.fix_buffer()


    @KeyRegister.register(r"\x0D")
    def carriage_return(self):
        self._curchar = 0
        self.fix_buffer()

    @KeyRegister.register(r"\x0E")
    def shift_out(self):
        pass

    @KeyRegister.register(r"\x0F")
    def shift_in(self):
        pass


###############
## Escape sequences
    @VT100Register.register(r"\x1b\[\??(?P<mode>\d*)(?P<property>(h|l))")
    def set_mode (self,mode = None, property =None): # <ESC>[? ... h or <ESC>[? ... m or <ESC>[? ...l

        if property == "m":
            if mode is None or mode == 0:
                self._attributes = {'bold':False, 'underline': False, 'blinking': False, 'low_intensity':False, 'invisible': False, 'reverse_video': False}
            elif mode == 1:
                self._attributes['bold'] = True
            elif mode == 2:
                self._attributes['low_intensity'] = True
            elif mode == 4:
                self._attributes['underline'] = True
            elif mode == 5:
                self._attributes['blinking'] = True
            elif mode == 7:
                self._attributes['reverse_video'] = True
            elif mode == 8:
                self._attributes['invisible'] = True


    @VT100Register.register(r"\x1b\[(?P<attributes>(\d+;)*\d*)m")
    def set_display_attr (self,attributes=None):
        pass
#        print "XXXXXXXX::: Setting display attr", attributes



    @VT100Register.register(r"\x1b\>")
    def set_numeric_keypad_mode (self): # <ESC>>
        pass

    @VT100Register.register(r"\x1b\=")
    def set_alternate_keypad_mode (self): # <ESC>=
        pass

    @VT100Register.register(r"\x1b(?P<paren>(\(|\)))(?P<val>(A|B|0|1|2))")
    def set_character_set (self,paren,val): # <ESC>=
        pass


    @VT100Register.register(r"\x1bN")
    def set_single_shift2 (self): # <ESC>N
        pass

    @VT100Register.register(r"\x1bO")
    def set_single_shift3 (self): # <ESC>O
        pass


    @VT100Register.register(r"\x1b\[(?P<line1>\d+);(?P<line2>\d+)r")
    def set_top_bottom_lines (self, line1, line2):
        self._topline = line1
        self._bottomline = line2
        self.fix_buffer()




    @VT100Register.register(r"\x1b\[(?P<count>\d+)A",r"\x1b\[A")
    def cursor_up (self,count=1): # <ESC>[{COUNT}A ## NOT: or <ESC> M 
        self._curline -= count
        if self._curline < 0: self._curline = 0


    @VT100Register.register(r"\x1b\[(?P<count>\d+)B",r"\x1b\[B")
    def cursor_down (self,count=1): # <ESC>[{COUNT}B (not confused with back)

        self._curline += count
        n = len(self._lines)
        if self._curline > n: self._lines += [""]*(self._curline - n)


    @VT100Register.register(r"\x1b\[(?P<count>\d+)C",r"\x1b\[C")
    def cursor_forward (self,count=1): # <ESC>[{COUNT}C
        self._curchar += count
        n = len(self._lines[self._curline])
        if self._curchar>n: self._lines[self._curline] += " "*(self._curchar - n)


    @VT100Register.register(r"\x1b\[(?P<count>\d+)D",r"\x1b\[D")
    def cursor_back (self,count=1): # <ESC>[{COUNT}D (not confused with down)
#        print "Cursor back"
        self._curchar -= count
        if self._curchar<0: self._curchar = 0



    @VT100Register.register(r"\x1b\[(?P<line>\d+);(?P<char>\d+)H", r"\x1b\[;?H")
    def cursor_home (self, line=1, char=1):
        self._curline = line
        self._curchar = char
        self.fix_buffer()

    @VT100Register.register(r"\x1b\[(?P<line>\d+);(?P<char>\d+)f",r"\x1b\[;?f")
    def cursor_force_position (self, line=1, char=1): # <ESC>[{ROW};{COLUMN}f
        self._curline = line
        self._curchar = char
        self.fix_buffer()

    @VT100Register.register(r"\x1b7")
    def cursor_save_attrs (self): # <ESC>7 
        self._home_line = self._curline
        self._home_char = self._curchar
        self._home_attributes = self._attributes

    @VT100Register.register(r"\x1b8")
    def cursor_restore_attrs (self): # <ESC>8 
        self._curline = self._home_line
        self._curchar = self._home_char
        self._attributes = self._home_attributes
        self.fix_buffer()



    @VT100Register.register(r"\x1bH")
    def set_tab (self): # <ESC>H
        pass

    @VT100Register.register(r"\x1b\[0?g")
    def clear_tab (self): # <ESC>[g
        pass

    @VT100Register.register(r"\x1b\[3g")
    def clear_all_tabs (self): # <ESC>[3g
        pass

    @VT100Register.register(r"(\x1b)#3")
    def double_letters_height_top_half (self): # <ESC>#3
        pass

    @VT100Register.register(r"(\x1b)#4")
    def double_letters_height_bottom_half (self): # <ESC>#4
        pass

    @VT100Register.register(r"(\x1b)#5")
    def single_width (self): # <ESC>#5
        pass

    @VT100Register.register(r"(\x1b)#6")
    def double_width (self): # <ESC>#6
        pass

    @VT100Register.register(r"(\x1b)#8")
    def screen_alignment_display (self): # <ESC>#8
        pass



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
        self.fix_buffer()

    ### TODO: Figure out which are terminal -> computer and vice versa
    @VT100Register.register(r"(\x1b)5n")
    def device_status_report (self): # <ESC>5n
#        print "Reset device"
        pass

    @VT100Register.register(r"(\x1b)0n") ## FIXME: RESPONSE TO PREVIOUS
    def terminal_ok (self): # <ESC>0n
#        print "Reset device"
        pass

    @VT100Register.register(r"(\x1b)3n") ## FIXME: RESPONSE TO PREVIOUS
    def terminal_not_ok (self): # <ESC>3n
#        print "Reset device"
        pass

    @VT100Register.register(r"(\x1b)6n")
    def get_cursor_position (self): # <ESC>3n
#        print "Reset device"
        pass

    @VT100Register.register(r"\x1b(?P<line>\d+);(?P<char>\d+);") ## FIXME: RESPONSE
    def respond_cursor_position (self): # <ESC>3n
#        print "Reset device"
        pass



    @VT100Register.register(r"\x1b\[c")
    def identify_terminal (self): # <ESC>c
#        print "Reset device"
        pass

    @VT100Register.register(r"\x1b\[0c")
    def identify_terminal_another (self): # <ESC>0c
#        print "Reset device"
        pass

    @VT100Register.register(r"\x1b\[1;0c") ## FIXME: RESPONSE
    def terminal_type_code (self): # <ESC>0c 
#        print "Reset device"
        pass



    @VT100Register.register(r"(\x1b)c")
    def reset_terminal (self): # <ESC>c
#        print "Reset device"
        pass


    @VT100Register.register(r"\x1b\[(?P<val>\d+)q")
    def switch_leds (self, val = 0): # <ESC>0q
#        print "Reset device"
        pass    



    @VT100Register.register(r"\x1b\]0;.*\x07")
    def unknown1 (self): # <ESC>]0;
#        print "UNKNOWN: <ESC>]0;"%variable
        pass
    @VT100Register.register(r"\x1b\[(?P<variable>\d+)d")
    def unknown2 (self, variable): # <ESC>]0;
#        print "UNKNOWN: <ESC>[%dd"%variable
        pass

    @VT100Register.register(r"\x1b\[(?P<variable>\d+)G")
    def unknown3 (self, variable): # <ESC>]0;
#        print "UNKNOWN: <ESC>[%dG"%variable
        pass




                      




if __name__ == "__main__":
    test = VT100Interpreter()
    test.write("Hello0\x1b[1D world\n!!!\x1b[2D\x1b[1A3");

