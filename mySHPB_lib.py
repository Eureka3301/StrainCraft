import os

def prnt(s = ''):
    print('=' * os.get_terminal_size().columns)
    print(s)

prnt('loading standard modules')
# ### Used Modules
import pandas as pd
import numpy as np
import json


import matplotlib.pyplot as plt
import seaborn as sns

prnt('standard modules loaded')

def df_dydx(df, x, y):
    '''
    calculates the derivative of y variable over x variable in the dataframe df
    '''
    return (df[y].shift(-1) - df[y])/(df[x].shift(-1) - df[x])

def df_int_ydx(df, x, y):
    '''
    calculates the Barrow integral (starting from the first x in dataframe.
    x values must be sorted) of y variable over x variable in the dataframe df
    with trapezoid method
    '''
    return (df[y].shift(-1)+df[y])/2*(df[x].shift(-1)-df[x])

class specimen():
    def __init__(self,
                    setupPropsFile,
                    dataDir,
                    rm_window = 50,
                    trig_start = 250, # mu s
                    **kwargs,
    ):

        '''
        This program parses data saved by new Rigol DS Oscilloscope.
        It contains raw Voltage(Time) dependences from two channels of the oscilloscope.
        '''

        if 'v/m//s' in kwargs:
            self.v0 = kwargs['v/m//s']
        else:
            self.v0 = None

        self.setupPropsFile = setupPropsFile
        # ### uploading json property file of the setup
        with open(setupPropsFile, 'r') as file:
            props = json.load(file)

        self.filename = dataDir + r'/' + kwargs['filename']
        # ### V(t) for CH1 & CH2 are loaded into df
        df = pd.read_csv(self.filename,
                        header=0,
                        names = ['Time/s', 'CH1/V', 'CH2/V']
        )

        df['Time/s'] -= df['Time/s'].iloc[0]
        df['Time/mus'] = df['Time/s']*1e+6

        df['CH1/V'] = -df['CH1/V']
        df['CH2/V'] = -df['CH2/V']


        # ### CH1/V/rm & CH2/V/rm ### rolling mean smoothing
        df['CH1/V/rm'] = df['CH1/V'].rolling(rm_window).mean()
        df['CH2/V/rm'] = df['CH2/V'].rolling(rm_window).mean()


        # ### CH1/V/zero & CH2V/zero ### balancing the bridges
        CH1_zero = df[df['Time/mus'].between(left=0, right=trig_start)]['CH1/V/rm'].mean()
        df['CH1/V/zero'] = df['CH1/V/rm'] - CH1_zero

        CH2_zero = df[df['Time/mus'].between(left=0, right=trig_start)]['CH2/V/rm'].mean()
        df['CH2/V/zero'] = df['CH2/V/rm'] - CH2_zero


        # ### Voltage on bridges to stress in the bars 
        # Let $\sigma = K \cdot V$
        K = props['K/MPa//mV'] # MPa/mV

        d = props['d/mm'] # mm
        S = np.pi*d*d/4 # mm2

        rho = props['rho/kg//m3'] # kg/m3
        E = props['E/GPa'] # GPa
        nu = props['nu']

        # ### The stress and strain pulses in the bars
        df['CH1/MPa'] = df['CH1/V/zero'] * K*1e+3
        df['CH2/MPa'] = df['CH2/V/zero'] * K*1e+3

        df['CH1/strain'] = df['CH1/MPa'] / E *1e-3
        df['CH2/strain'] = df['CH2/MPa'] / E * 1e-3

        # ### start of incident, transmitted, reflected pulses
        # We find the beginning of the incident pulse by the prevailing of "zero" level (noiseZero MPa).
        noiseZero = 0.6*K # MPa

        i_start = df[df['CH1/MPa'] > noiseZero].index[0]


        # The shift to syncronise gauges is evaluated by their position on bars.
        # As we have time grid inherited from the discretisation of the oscilloscope
        # the shift will be produced according to it.
        c = np.sqrt(E/rho*1e+9) # m/s
        L1 = props['L1/m'] # m
        L2 = props['L2/m'] # m

        dtR = 2*L1/c*1e+6 # mus
        dtT = (L1+L2)/c*1e+6 # mus
        dtI = df.loc[i_start]['Time/mus'] # mus

        r_start = df[df['Time/mus'] > dtI+dtR].index[0]
        t_start = df[df['Time/mus'] > dtI+dtT].index[0]

        dfI = df[['Time/mus', 'CH1/MPa']].copy()
        dfR = df[['Time/mus', 'CH1/MPa']].copy()
        dfT = df[['Time/mus', 'CH2/MPa']].copy()

        dfI['Time/mus'] = dfI['Time/mus'].shift(i_start)
        dfR['Time/mus'] = dfR['Time/mus'].shift(r_start)
        dfT['Time/mus'] = dfT['Time/mus'].shift(t_start)

        striker = props['striker/cm'] # cm
        T = 2*striker*1e-2 / c * 1e+6 # mus

        dfI = dfI[dfI['Time/mus']<T].dropna()
        dfT = dfT[dfT['Time/mus']<T].dropna()
        dfR = dfR[dfR['Time/mus']<T].dropna()


        # ### dfP is dataframe with synchronised pulses
        # We merge them by their "times".
        dfP = pd.merge(left=dfI, right=dfR, how='inner',
                        left_on='Time/mus', right_on='Time/mus', suffixes=('_I','_R'))

        dfP = pd.merge(left=dfP, right=dfT, how='inner',
                        left_on='Time/mus', right_on='Time/mus', suffixes=('_P','_T'))

        new_names = {
            'CH1/MPa_I':'I/MPa',
            'CH1/MPa_R':'R/MPa',
            'CH2/MPa':'T/MPa',
        }

        dfP.rename(columns=new_names, inplace=True)

        dfP['T-R/MPa'] = dfP['T/MPa'] - dfP['R/MPa']


        # ### Stress(t) and Strain(t)
        Ls = kwargs['H_s/mm'] # mm
        Ds = kwargs['D_s/mm'] # mm

        As = np.pi*Ds*Ds/4 # mm2

        # average stress in the specimen
        # dfP['Stress/MPa'] = 1/2*S/As*(dfP['I/MPa']+dfP['R/MPa']+dfP['T/MPa'])
        # stress going through the specimen
        dfP['Stress/MPa'] = S/As*(dfP['T/MPa'])
        dfP['I-R-T/MPa'] = dfP['I/MPa']-dfP['R/MPa']-dfP['T/MPa']
        dfP['dotStrain'] = c/Ls*1e+3 * 1e-9/E * (dfP['I/MPa']-dfP['R/MPa']-dfP['T/MPa'])*1e+6
        dfP['dStrain'] = df_int_ydx(dfP, y='dotStrain', x='Time/mus')*1e-6
        dfP['Strain'] = dfP['dStrain'].cumsum()

        dfP[['Time/mus', 'dotStrain', 'dStrain', 'Strain']].head()

        self.strainRate = round(dfP['dotStrain'].mean()/100.0)*100


        # ### d sigma / d epsilon. Specimen unloading cutting
        dfP['E(eps)/MPa'] = df_dydx(dfP, y='Stress/MPa', x='Strain')
        dfP['E(eps)/MPa'] = dfP['E(eps)/MPa'].rolling(rm_window).mean()
        unload = dfP['E(eps)/MPa'].idxmin()

        dfP.drop(dfP.iloc[unload:].index, inplace=True)

        # ### Calculating True Stress and Strain
        dfP['StrainTrue'] = -np.log(1-dfP['Strain'])
        dfP['StressTrue/MPa'] = dfP['Stress/MPa']*(1-dfP['Strain'])

        # ### Saving all the info we may need
        self.dfP = dfP[['Time/mus', 'I/MPa', 'R/MPa', 'T/MPa', 'T-R/MPa', 'dotStrain', 'Strain', 'Stress/MPa', 'StrainTrue', 'StressTrue/MPa']]

        # ### Printing to terminal some info at the end of preprocessing
        # ### To calm down the nerves
        if '№' in kwargs:
            prnt(kwargs['№'])
        prnt(f'K = {K} MPa/mV, striker length = {striker} cm, impact velocity = {self.v0} m/s')
        prnt(f'Strain Rate = {self.strainRate:.0f} 1/s')
        

    def plot_diagrams(self,
                        nosave = True,
                        single = True,
    ):
        sns.lineplot(data = self.dfP,
                        x = 'StrainTrue',
                        y='StressTrue/MPa',
                        label = f'True diagram',
                    )
        sns.lineplot(data = self.dfP,
                        x = 'Strain',
                        y='Stress/MPa',
                        label = f'Engineering diagram',
                    )
        
        if nosave == True:
            if single:
                plt.show()
        else:
            plt.savefig('diagrams.jpg')
    
    def plot_diagram(self,
                        nosave = True,
                        single = True,
    ):
        sns.lineplot(data = self.dfP,
                        x = 'StrainTrue',
                        y='StressTrue/MPa',
                        label = f'Strain Rate {self.strainRate:.0f} 1/s',
                    )
        if nosave == True:
            if single:
                plt.show()
        else:
            plt.savefig('diagram.jpg')

    def plot_balance(self,
                        nosave = True,
                        single = True,
    ):
        sns.lineplot(data=self.dfP,
                    x = 'Time/mus',
                    y = 'I/MPa',
                    label = 'Incident',)

        sns.lineplot(data=self.dfP,
                        x = 'Time/mus',
                        y = 'R/MPa',
                        label = 'Reflected',)

        sns.lineplot(data=self.dfP,
                        x = 'Time/mus',
                        y = 'T/MPa',
                        label = 'Transmitted',)

        sns.lineplot(data=self.dfP,
                        x = 'Time/mus',
                        y = 'T-R/MPa',
                        label = 'Transmitted-Reflected',)

        if nosave == True:
            if single:
                plt.show()
        else:
            plt.savefig('balance.jpg')


class expSeries():
    def __init__(self,
                    NBfilename,
                    setupPropsFile,
                    dataDir,
                    **kwargs,
    ):
        self.NBfilename = dataDir+ r'/' +NBfilename
        # ### reading the experimental notes
        self.df = pd.read_excel(self.NBfilename,
                            header=0,                      
        )
        records = self.df.to_dict(orient = 'records')

        # ### creating all tested specimens        
        self.tests = [specimen(setupPropsFile, dataDir = dataDir, **records[i]) for i in range(len(self.df.index))]

        self.df['strainRate/1//s'] = [self.tests[i].strainRate for i in range(len(self.df.index))]

        # ### printing the notes
        prnt()
        print(self.df)

    def sortByStrainRate(self):
        self.df.sort_values(by=['strainRate/1//s'], inplace=True)
    def sortByNum(self):
        self.df.sort_values(by=['№'], inplace=True)

    def prnt(self):
        prnt()
        print(self.df)

    def plot_diagrams(self, nums, single = False):
        for num in nums:
            self.tests[num].plot_diagram(single=single)

    def cheerUP(self):
        prnt('Doing great, man!')
