import pyalps
import matplotlib.pyplot as plt
import pyalps.plot
import sys

print "Starting"

parms = []
for t in [1.5,2,2.5]:
   parms.append(
       { 
         'LATTICE'        : "square lattice", 
         'T'              : t,
         'J'              : 1 ,
         'THERMALIZATION' : 1000,
         'SWEEPS'         : 100000,
         'UPDATE'         : "cluster",
         'MODEL'          : "Ising",
         'L'              : 8
       }
   )

input_file = pyalps.writeInputFiles('parm1',parms)
desc = pyalps.runApplication('spinmc',input_file,Tmin=5,writexml=True)

result_files = pyalps.getResultFiles(prefix='parm1')
print result_files
print pyalps.loadObservableList(result_files)
data = pyalps.loadMeasurements(result_files,['|Magnetization|','Magnetization^2'])
print data
plotdata = pyalps.collectXY(data,'T','|Magnetization|')
plt.figure()
pyalps.plot.plot(plotdata)
plt.xlim(0,3)
plt.ylim(0,1)
plt.title('Ising model')
plt.show()
print pyalps.plot.convertToText(plotdata)
print pyalps.plot.makeGracePlot(plotdata)
print pyalps.plot.makeGnuplotPlot(plotdata)
binder = pyalps.DataSet()
binder.props = pyalps.dict_intersect([d[0].props for d in data])
binder.x = [d[0].props['T'] for d in data]
binder.y = [d[1].y[0]/(d[0].y[0]*d[0].y[0]) for d in data]
print binder
plt.figure()
pyalps.plot.plot(binder)
plt.xlabel('T')
plt.ylabel('Binder cumulant')
plt.show()
