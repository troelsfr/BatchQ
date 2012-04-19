from batchq.core.template import Template
from batchq.core.library import Library


class PlainTextTemplate(Template):
    code_block_start = r"/*:"
    code_block_end = r":*/"
    partial_code_start = r"//:"
    partial_code_end = r"//!"
    variable_start = r"{{"
    variable_end = r"}}"    
    string_start = "\""
    string_end = "\""    

    conversions = {"/*:":"/\*:",  ":*/": ":\*/", "//:": "//:", "//!": "//!", "{{": "\{\{", "}}": "\}\}","\"": "\""}


class CppTemplate(Template):
    code_block_start = r"/*:"
    code_block_end = r":*/"
    partial_code_start = r"//:"
    partial_code_end = r"//!"
    variable_start = r"{{"
    variable_end = r"}}"    
    string_start = "\""
    string_end = "\""    

    conversions = {"/*:":"/\*:",  ":*/": ":\*/", "//:": "//:", "//!": "//!", "{{": "\{\{", "}}": "\}\}","\"": "\""}



class TeXTemplate(Template):
    code_block_start = r"% [["
    code_block_end = r"% ]]"
    partial_code_start = r"% $"
    partial_code_end = r"% !"
    variable_start = r"{%%"
    variable_end = r"%%}"    
    string_start = "\""
    string_end = "\""    

    conversions = {r"% $":r"% \$",r"% !":r"% \!",r"% [[":r"% \[\[",  r"% ]]": r"% \]\]", "//:": "//:", "//!": "//!", "{%%": "\{%%", "%%}": "%%\}","\"": "\""}


Library.templates.register("tex",TeXTemplate)
Library.templates.register("txt",PlainTextTemplate)
Library.templates.register("c",CppTemplate)
Library.templates.register("h",CppTemplate)
Library.templates.register("cpp",CppTemplate)
Library.templates.register("hpp",CppTemplate)


