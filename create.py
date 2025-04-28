from mySHPBlib import sample

wrkdir = 'Mg_11.03'
nbFilename = 'Mg_11.03.xlsx'
propFilename = 'properties.json'

sample1 = sample(wrkdir=wrkdir, nbFilename=nbFilename, propFilename=propFilename)

# ### saving calculated data

import pickle

with open('dump.pickle', 'wb') as file:
    pickle.dump(sample1, file)



from mySHPBlib import sample, prnt

import pickle

prnt('loading data')

with open('dump.pickle', 'rb') as file:
    sample1 = pickle.load(file)

prnt('data loaded')

print(sample1.nb.head())

sample1.specimens[0].plot_balance()