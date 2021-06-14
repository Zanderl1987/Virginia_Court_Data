import numpy as np
from scipy.stats import variation
from decimal import *

pepe = [1.2, 1, 0, 10, 15]
a = np.array(pepe)

cv = variation(a)

test = ((a<=10) & (a>=0)).sum()

# print(np.nan*a)

pepe = [{'value': Decimal('112.1628533991'), 'time': 1546318800}, 
{'value': Decimal('112.2093277904'), 'time': 1546319100}, 
{'value': Decimal('112.3063316169'), 'time': 1546319400}, 
{'value': Decimal('112.4270280374'), 'time': 1546319700}, 
{'value': Decimal('112.5595020390'), 'time': 1546320000}, 
{'value': Decimal('112.6968263679'), 'time': 1546320300}]

# print(np.where((a>0) & (a<15)))
# print(a[(np.where((a>0) & (a<15)))])

pepe = np.array([125.68,202.82,121.32])
print(np.nanpercentile(pepe,25,interpolation='linear'))