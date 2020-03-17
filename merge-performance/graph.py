#!/usr/bin/env python3

#from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np

x = np.arange(2)
#money = [1.5e5, 2.5e6, 5.5e6, 2.0e7]
timings = [5977.214, 31.815]


#def millions(x, pos):
#    'The two args are the value and tick position'
#    return '$%1.1fM' % (x * 1e-6)
#formatter = FuncFormatter(millions)
fig, ax = plt.subplots()
#ax.yaxis.set_major_formatter(formatter)

plt.bar(x, timings)
logscale = False
if logscale:
  ax.set_yscale('log')
  plt.yticks((10, 100, 1000, 10000), ('1', '2', '3', '4'))
  plt.ylabel('log$_{10}$(seconds)')
else:
  plt.ylabel('seconds')
plt.xticks(x, ('git-2.25.0 (Before)', 'git-devel (After)'))
plt.title('Rebase 35 patches after renaming drivers/ $\Rightarrow$ pilots/')
plt.savefig('timing.pdf')
#plt.show()


#N = 5
#menMeans = (20, 35, 30, 35, 27)
#womenMeans = (25, 32, 34, 20, 25)
#menStd = (2, 3, 4, 1, 2)
#womenStd = (3, 5, 2, 3, 3)
#ind = np.arange(N)    # the x locations for the groups
#width = 0.35       # the width of the bars: can also be len(x) sequence
#
#p1 = plt.bar(ind, menMeans, width, yerr=menStd)
#p2 = plt.bar(ind, womenMeans, width,
#             bottom=menMeans, yerr=womenStd)
#
#plt.ylabel('Scores')
#plt.title('Scores by group and gender')
#plt.xticks(ind, ('G1', 'G2', 'G3', 'G4', 'G5'))
#plt.yticks(np.arange(0, 81, 10))
#plt.legend((p1[0], p2[0]), ('Men', 'Women'))
#
#plt.show()
