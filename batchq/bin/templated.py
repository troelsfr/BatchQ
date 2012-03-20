#!/usr/bin/python
import sys
from batchq.templates import TEMPLATE_REGISTER

class Main:
    def __call__(self,args, context = {}):    
        print args
        try:
            me, engine, infile, outfile = args
        except:
            print "Usage: %s [engine] [input file] [output file]" % args[0]
            return -1

        if not engine in TEMPLATE_REGISTER:
            print "Engine not found."
            return -2

        eng = TEMPLATE_REGISTER[engine]
        
        f = open(infile, "r+")
        input = f.read()
        f.close()

        ctx = __import__('batchq.core.batch')
        print ctx
    
        output = eng(input).render(context)
        
        f = open(outfile, "w")
        f.write(output)
        f.close()
    

if __name__ == "__main__":
    main = Main()
    sys.exit(main(sys.argv))
