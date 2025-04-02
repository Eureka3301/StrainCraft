from mySHPB_lib import specimen, expSeries

NBfilename = 'Mg_11.03.xlsx'
dataDir = 'Mg_11.03'

NB = expSeries(
                NBfilename=NBfilename,
                setupPropsFile='props2025march.json',
                dataDir = dataDir,
)

NB.cheerUP()