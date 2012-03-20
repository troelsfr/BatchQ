from batchq.bin import Main
from batchq.pipelines.shells.bash import BashTerminal
from batchq.corre.batch import Controller

class Provenence(object):
    def __init__(self, build="_build/", url=None ):
        self._mainclass = []
        self._url = url
        self._build = build

    def registerClass(self, cls):
        self._mainclass.append(cls())

    def setSection(self,title):
        self._section = title

    def setSubSection(self,title):
        self._sub_section = title

    def setTask(self,title):
        self._task = title

    def setLocation(self,title):
        self._section = section
        self._sub_section = subsection
        self._task = task


    def listDependencies(self):
        dependencies = []
        if len(dependencies) == 1:
            return dependencies[0]
        return ", ".join(dependencies[0:-1]) + " and " + dependencies[-1]       

    def suplementary(self):
        return self._url

    def webadress(self, url):
        self._url = url

    def build(self, build):
        self._build = build


if __name__ == "__main__":
    # input texfile, HTML directory = ,     
    ctx = {'__directory__':os.getcwd(), 'document': Provenence(), 'TerminalInstance': Controller(BashTerminal)  }
    main = Main(ctx)
    main(sys.argv)

    sys.exit()

