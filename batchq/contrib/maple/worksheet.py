from xml.etree.ElementTree import ElementTree
def load_input(filename, pipe):
    tree = ElementTree()
    
    tree.parse(filename)
    
        
    def parseTree(root,pipe):
        if "input-equation" in root.attrib:
            pipe.send_command(root.attrib["input-equation"])

        for child in list(root):
            parseTree(child, pipe)
    parseTree(tree.getroot(), pipe)
