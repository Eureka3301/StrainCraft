from mySHPB_lib import specimen, expSeries

NBfilenames = [
    'Mg_11.03.xlsx',
    'Mg_14.03.xlsx',
]

dataDirs = [
    'Mg_11.03',
    'Mg_14.03'
]

n = 2

NBs = []

for i in range(n):
    NBs.append(
        expSeries(
                    NBfilename=NBfilenames[i],
                    setupPropsFile='props2025march.json',
                    dataDir = dataDirs[i],
        )
    )
    NBs[i].sortByStrainRate()