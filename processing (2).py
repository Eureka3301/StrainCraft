import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline

def preprocessing(filename, testNumber, voltage_file):
    # ### V(t) for CH1 & CH2 in df


    df = pd.read_csv(filename,
                    header=0,
                    names = ['Time/s', 'CH1/V', 'CH2/V']
    )

    df['Time/s'] -= df['Time/s'].iloc[0]
    df['Time/mus'] = df['Time/s']*1e+6

    df['CH1/V'] = -df['CH1/V']
    df['CH2/V'] = -df['CH2/V']


    #Multiply by the voltage coeff

    Vdf = pd.read_csv(voltage_file, names=['V_1', 'V_2'])

    df['CH1/V'] = df['CH1/V'] * (20 / Vdf['V_1'].iloc[testNumber])
    df['CH2/V'] = df['CH2/V'] * (20 / Vdf['V_2'].iloc[testNumber])

    # ### CH1/V/rm/50 & CH2/V/rm/50

    df['CH1/V/rm/50'] = df['CH1/V'].rolling(50).mean()
    df['CH2/V/rm/50'] = df['CH2/V'].rolling(50).mean()

    # ### CH1/V/zero & CH2V/zero

    trig_start = 100 # mu s

    CH1_zero = df[df['Time/mus'].between(left=0, right=trig_start)]['CH1/V/rm/50'].mean()
    df['CH1/V/zero'] = df['CH1/V/rm/50'] - CH1_zero

    CH2_zero = df[df['Time/mus'].between(left=0, right=trig_start)]['CH2/V/rm/50'].mean()
    df['CH2/V/zero'] = df['CH2/V/rm/50'] - CH2_zero

    df.drop(columns=['Time/s','CH1/V', 'CH2/V', 'CH1/V/rm/50','CH2/V/rm/50'], inplace=True)


    return df

def pulses(df, Ls, Ds,striker_cm):
    # Let $\varepsilon = K \cdot V$, $K_{exp}$ - experimental coefficient and $K_{th}$ - theoretical coefficient.

    d = 20  # mm
    S = np.pi * d * d / 4  # mm2

    rho = 8300  # kg/m3
    E = 220  # GPa

    Kexp_new = 10  # MPa/mV
    #print('Kexp = %.2f MPa/mV, Kth = %.2f MPa/mV' % (Kexp, Kth))

    # ### The stress and strain pulses

    df['CH1/MPa'] = df['CH1/V/zero'] * Kexp_new * 1e+3
    df['CH2/MPa'] = df['CH2/V/zero'] * Kexp_new * 1e+3

    df['CH1/strain'] = df['CH1/MPa'] / E * 1e-3
    df['CH2/strain'] = df['CH2/MPa'] / E * 1e-3


    # ### start of i, t, r pulses

    # We find the beginning of the incident pulse by the prevailing of "zero" level (10 MPa).

    dfI = df[['Time/mus', 'CH1/MPa']].copy()
    dfR = df[['Time/mus', 'CH1/MPa']].copy()
    dfT = df[['Time/mus', 'CH2/MPa']].copy()

    noiseZero = 10  # MPa
    i_start = df[df['CH1/MPa'] > noiseZero].index[0]
    t_start = df[df['CH2/MPa'] > noiseZero].index[0]
    r_start = df[df['CH1/MPa'] < -noiseZero].index[0]

    dfI['Time/mus'] = dfI['Time/mus'].shift(i_start)
    dfR['Time/mus'] = dfR['Time/mus'].shift(r_start)
    dfT['Time/mus'] = dfT['Time/mus'].shift(t_start)


    c = np.sqrt(E / rho * 1e+9)  # m/s
    T = 2 * striker_cm * 1e-2 / c * 1e+6 + 10  # mus

    dfI = dfI[dfI['Time/mus'] < T].dropna()
    dfT = dfT[dfT['Time/mus'] < T].dropna()
    dfR = dfR[dfR['Time/mus'] < T].dropna()

    # ### dfP synchronised pulses

    # We merge them by their "times".

    dfP = pd.merge(left=dfI, right=dfR, how='inner',
                   left_on='Time/mus', right_on='Time/mus', suffixes=('_I', '_R'))
    dfP = pd.merge(left=dfP, right=dfT, how='inner',
                   left_on='Time/mus', right_on='Time/mus', suffixes=('_P', '_T'))

    new_names = {
        'CH1/MPa_I': 'I/MPa',
        'CH1/MPa_R': 'R/MPa',
        'CH2/MPa': 'T/MPa',
    }

    dfP.rename(columns=new_names, inplace=True)

    # ### Stress(t) and Strain(t)


    As = np.pi * Ds * Ds / 4  # mm2

    dfP['Stress/MPa'] = 0.5 * (S / As) * (dfP['T/MPa'] + dfP['I/MPa'] + dfP['R/MPa'])

    dfP['I-R-T/MPa'] = dfP['I/MPa'] - dfP['R/MPa'] - dfP['T/MPa']
    dfP['dotStrain'] = (c / Ls) * (1e-9 / E) * (dfP['I/MPa'] - dfP['R/MPa'] - dfP['T/MPa']) * 1e+6

    I_R_T = CubicSpline(dfP['Time/mus'], dfP['I-R-T/MPa'])

    TimeArr = dfP['Time/mus'].to_numpy()
    StrainArr = np.ones(dfP['Time/mus'].size)

    for i in range(dfP['Time/mus'].size):
        StrainArr[i] = (c / Ls) * (1e-9 / E) * I_R_T.integrate(0, TimeArr[i])

    dfP['Strain'] = StrainArr

    strainRate = dfP['dotStrain'].mean()

    # ### d sigma / d epsilon. Specimen unloading

    dfP['E(eps)/MPa'] = (dfP['Stress/MPa'].shift(-1) - dfP['Stress/MPa']) / (dfP['Strain'].shift(-1) - dfP['Strain'])
    dfP['E(eps)/MPa'] = dfP['E(eps)/MPa'].rolling(100).mean()
    unload = dfP['E(eps)/MPa'].idxmin()

    dfP.drop(dfP.iloc[unload:].index, inplace=True)

    dfP['StrainTrue'] = -np.log(1 - dfP['Strain'])
    dfP['StressTrue/MPa'] = dfP['Stress/MPa'] * (1 - dfP['Strain'])

    dfP.drop(columns = ['I/MPa', 'R/MPa', 'T/MPa','I-R-T/MPa'], axis=1, inplace=True)

    return dfP, strainRate


def Sigma_dotEpsilon_dots(dfP,strainRate):

    dfP['Stress/MPa/mean'] = dfP['StressTrue/MPa'].rolling(10).mean()
    y = dfP['Stress/MPa/mean'].max()
    x = strainRate
    return x,y


def ultimateStress_dotEpsilon():
    TestData = pd.read_csv(r'D:\python\pythonProject\SHPB\Mg_test.csv', sep = ';', usecols = [9])
    TestData = TestData[TestData['Comment']=='destroyed']

    first = 0
    last = 9
    filenames1 = [r'C:\Users\mamki\Mg_11.03\RigolDS%d.csv' % i for i in range(first, last + 1)]

    first = 1
    last = 22
    filenames2 = [r'C:\Users\mamki\Mg_14.03\Mg%d.csv' % i for i in range(first, last + 1)]

    first = 1
    last = 18
    filenames3 = [r'C:\Users\mamki\Mg_21.03\Mg%d.csv' % i for i in range(first, last + 1)]

    filenames = filenames1 + filenames2 + filenames3;

    rows_count = TestData.shape[0]
    x = np.empty(rows_count)
    y = np.empty(rows_count)
    k = 0

    for i in TestData.index:
        # получаем данные
        df = preprocessing(filenames[i], i)
        dfP, strainRate = pulses(df)

        dfP['Stress/MPa/mean'] = dfP['StressTrue/MPa'].rolling(10).mean()

        y[k] = dfP['Stress/MPa/mean'].max()
        x[k] = strainRate
        k = k+1

    return x, y


