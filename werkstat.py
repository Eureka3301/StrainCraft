import pickle
import matplotlib.pyplot as plt
import seaborn as sns

with open('pickle.bin', 'rb') as file:
    NBs = pickle.load(file)

import pandas as pd

jointNB = pd.concat([NBs[0].df.sort_values(by=['№']), NBs[1].df.sort_values(by=['№'])]).reset_index(drop=True).sort_values(by=['strainRate/1//s'])

jointTest = NBs[0].tests + NBs[1].tests

similiar = {
    900 : [1,15],
    1100: [5,16],
    1300: [2,13],
    1400: [6,18],
    1700: [27,28],
    1800: [3,7,26,30,31],
}


for num in similiar[900]:
    
    sns.lineplot(data = jointTest[num].dfP,
                        x = 'StrainTrue',
                        y='StressTrue/MPa',
                        label = f'{num}, Strain Rate {jointTest[num].strainRate:.0f} 1/s',
                    )

plt.show()