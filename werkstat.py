import pickle
import matplotlib.pyplot as plt

with open('pickle.bin', 'rb') as file:
    NBs = pickle.load(file)

import pandas as pd

jointNB = pd.concat([NBs[0].df.sort_values(by=['№']), NBs[1].df.sort_values(by=['№'])]).reset_index(drop=True).sort_values(by=['strainRate/1//s'])

jointTest = NBs[0].tests + NBs[1].tests

print(list(jointNB.index))
for num in list(jointNB.index):
    jointTest[num].plot_diagram(single=False)

plt.show()