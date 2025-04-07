import pandas as pd

def upload_Newgorod():
    dfs = []

    N = 9

    filename = 'Нижний Новгород\Магний СПбГУ.xls'

    # ## sorted by strain rates

    sheets = [f'c744-0{i}' for i in [3,4,9,8,5,7,6,2,1]]


    strainRates = [
        985,
        1246,
        1326,
        1346,
        1362,
        1471,
        1627,
        1839,
        3281,
    ]

    strainRates = [round(r/10.0)*10 for r in strainRates]

    for sheet in sheets:
        dfs.append(
            pd.read_excel(
                io = filename,
                sheet_name=sheet,
                usecols=['деф(лог)','напр(ист)МПа'],
            ).rename(columns={'деф(лог)':'StrainTrue','напр(ист)МПа':'StressTrue/MPa'})
        )

    return N, dfs, strainRates