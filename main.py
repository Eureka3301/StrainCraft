from mySHPB_lib import SHPB_test

test_props = {
    "filename": 'exp\Mg_11.03\RigolDS9.csv',
    "setupPropsFile": 'props2025march.json',
    "Ls/mm": 4.0,
    "Ds/mm": 7.8
}

exp = SHPB_test(**test_props)

import matplotlib.pyplot as plt

exp.plot_diagrams()
plt.show()

exp.plot_diagram()
plt.show()