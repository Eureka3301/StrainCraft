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


# ## plotting similiar stress-strain curves

# for num in similiar[1800]:
    
#     sns.lineplot(data = jointTest[num].dfP,
#                         x = 'StrainTrue',
#                         y='StressTrue/MPa',
#                         label = f'{num}, Strain Rate {jointTest[num].strainRate:.0f} 1/s',
#                     )

# plt.show()

##################################

# ## plotting Newgorod strain rate curves

# strainRates = [
#         985,
#         1246,
#         1326,
#         1346,
#         1362,
#         1471,
#         1627,
#         1839,
#         3281,
#     ]

# from Newgorod import upload_Newgorod

# N, NGdfs, strainRate = upload_Newgorod()

# for n in range(N):
#     sns.lineplot(data=NGdfs[n],
#                  x = 'StrainTrue',
#                  y='StressTrue/MPa',
#                  label = f'Strain Rate {strainRate[n]} 1/s',
#                  )
    
# plt.show()

###################################

# ## plotting Newgorod and ours

from Newgorod import upload_Newgorod

N, NGdfs, strainRate = upload_Newgorod()


similiarOursNums = [
    [15,1,11,16,5],
    [17],
    [13],
    [2],
    [2],
    [6,19],
    [10],
    [31],
    [24],
]

for n in range(N):
    sns.lineplot(data=NGdfs[n],
                 x = 'StrainTrue',
                 y='StressTrue/MPa',
                 label = f'NG - Strain Rate {strainRate[n]} 1/s',
                 )
    for num in similiarOursNums[n]:
        sns.lineplot(data = jointTest[num].dfP,
                x = 'StrainTrue',
                y='StressTrue/MPa',
                label = f'{num}, Strain Rate {jointTest[num].strainRate:.0f} 1/s',
            )
    plt.show()