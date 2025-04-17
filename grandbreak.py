import pickle
import matplotlib.pyplot as plt
import seaborn as sns

with open('pickle.bin', 'rb') as file:
    NBs = pickle.load(file)

import pandas as pd

jointNB = pd.concat([NBs[0].df.sort_values(by=['№']), NBs[1].df.sort_values(by=['№'])]).reset_index(drop=True).sort_values(by=['strainRate/1//s'])

jointTest = NBs[0].tests + NBs[1].tests


for num in range(len(NBs[0].tests)):
    sns.lineplot(data = NBs[0].tests[num].dfP,
            x = 'StrainTrue',
            y='StressTrue/MPa',
            label = f'{num}, Strain Rate {NBs[0].tests[num].strainRate:.0f} 1/s',
        )

plt.show()