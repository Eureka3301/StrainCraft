import os
import pandas as pd
import numpy as np

def prnt(s = ''):
    print('=' * os.get_terminal_size().columns)
    print(s)

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

class Specimen():
    def __init__(self, **kwargs):

        '''
        This program parses data saved by new Rigol DS Oscilloscope.
        It contains raw Voltage(Time) dependences from two channels of the oscilloscope.
        '''

        self.df = pd.read_csv(
            kwargs['filename'],
            header=0,
            names = ['Time/s', 'CH1/V', 'CH2/V']
            )

        self.filter(**kwargs)

        self.shift(**kwargs)

        self.scale(**kwargs)

        self.syncronise(**kwargs)

        self.mechanics(**kwargs)

        # ### Printing to terminal some info at the end of preprocessing
        # ### To calm down the nerves
        if '№' in kwargs:
            prnt(kwargs['№'])
        prnt(f'Strain Rate = {self.strainRate:.0f} 1/s')


    def filter(self, **kwargs):
        self.df['CH1/V'] = -self.df['CH1/V']
        self.df['CH2/V'] = -self.df['CH2/V']
        # ### CH1/V/rm & CH2/V/rm ### rolling mean smoothing
        self.df['CH1/V/rm'] = self.df['CH1/V'].rolling(kwargs['rm_window']).mean()
        self.df['CH2/V/rm'] = self.df['CH2/V'].rolling(kwargs['rm_window']).mean()

    def shift(self, **kwargs):
        self.df['Time/s'] -= self.df['Time/s'].iloc[0]
        self.df['Time/mus'] = self.df['Time/s']*1e+6

        # ### CH1/V/zero & CH2V/zero ### balancing the bridges
        CH1_zero = self.df[self.df['Time/mus'].between(left=0, right=kwargs['trig_start'])]['CH1/V/rm'].mean()
        self.df['CH1/V/zero'] = self.df['CH1/V/rm'] - CH1_zero

        CH2_zero = self.df[self.df['Time/mus'].between(left=0, right=kwargs['trig_start'])]['CH2/V/rm'].mean()
        self.df['CH2/V/zero'] = self.df['CH2/V/rm'] - CH2_zero

    def scale(self, **kwargs):
        # ### Voltage on bridges to stress in the bars 
        # Let $\sigma = K \cdot V$
        K = kwargs['K/MPa//mV'] # MPa/mV

        d = kwargs['d/mm'] # mm
        S = np.pi*d*d/4 # mm2
        rho = kwargs['rho/kg//m3'] # kg/m3
        E = kwargs['E/GPa'] # GPa
        c = np.sqrt(E/rho*1e+9) # m/s

        rho = kwargs['rho/kg//m3'] # kg/m3
        E = kwargs['E/GPa'] # GPa

        # ### The stress and strain pulses in the bars
        self.df['CH1/MPa'] = self.df['CH1/V/zero'] * K*1e+3
        self.df['CH2/MPa'] = self.df['CH2/V/zero'] * K*1e+3

        self.df['CH1/strain'] = self.df['CH1/MPa'] / E *1e-3
        self.df['CH2/strain'] = self.df['CH2/MPa'] / E * 1e-3

    def syncronise(self, **kwargs):
        # ### start of incident, transmitted, reflected pulses
        # We find the beginning of the incident pulse by the prevailing of "zero" level (noiseZero MPa).
        noiseZero = kwargs['zeroCoef']*kwargs['K/MPa//mV'] # MPa

        i_start = self.df[self.df['CH1/MPa'] > noiseZero].index[0]

        # The shift to syncronise gauges is evaluated by their position on bars.
        # As we have time grid inherited from the discretisation of the oscilloscope
        # the shift will be produced according to it.
        rho = kwargs['rho/kg//m3'] # kg/m3
        E = kwargs['E/GPa'] # GPa
        c = np.sqrt(E/rho*1e+9) # m/s
        L1 = kwargs['L1/m'] # m
        L2 = kwargs['L2/m'] # m

        dtR = 2*L1/c*1e+6 # mus
        dtT = (L1+L2)/c*1e+6 # mus
        dtI = self.df.loc[i_start]['Time/mus'] # mus

        r_start = self.df[self.df['Time/mus'] > dtI+dtR].index[0]
        t_start = self.df[self.df['Time/mus'] > dtI+dtT].index[0]

        dfI = self.df[['Time/mus', 'CH1/MPa']].copy()
        dfR = self.df[['Time/mus', 'CH1/MPa']].copy()
        dfT = self.df[['Time/mus', 'CH2/MPa']].copy()

        dfI['Time/mus'] = dfI['Time/mus'].shift(i_start)
        dfR['Time/mus'] = dfR['Time/mus'].shift(r_start)
        dfT['Time/mus'] = dfT['Time/mus'].shift(t_start)

        striker = kwargs['striker/cm'] # cm
        T = 2*striker*1e-2 / c * 1e+6 # mus

        dfI = dfI[dfI['Time/mus']<T].dropna()
        dfT = dfT[dfT['Time/mus']<T].dropna()
        dfR = dfR[dfR['Time/mus']<T].dropna()


        # ### dfP is dataframe with synchronised pulses
        # We merge them by their "times".
        self.dfP = pd.merge(left=dfI, right=dfR, how='inner',
                        left_on='Time/mus', right_on='Time/mus', suffixes=('_I','_R'))

        self.dfP = pd.merge(left=self.dfP, right=dfT, how='inner',
                        left_on='Time/mus', right_on='Time/mus', suffixes=('_P','_T'))

        new_names = {
            'CH1/MPa_I':'I/MPa',
            'CH1/MPa_R':'R/MPa',
            'CH2/MPa':'T/MPa',
        }

        self.dfP.rename(columns=new_names, inplace=True)

        self.dfP['I+R/MPa'] = self.dfP['I/MPa'] + self.dfP['R/MPa']

    def mechanics(self, **kwargs):
        # ### Stress(t) and Strain(t)
        Ls = kwargs['H_s/mm'] # mm
        Ds = kwargs['D_s/mm'] # mm

        d = kwargs['d/mm'] # mm
        S = np.pi*d*d/4 # mm2
        rho = kwargs['rho/kg//m3'] # kg/m3
        E = kwargs['E/GPa'] # GPa
        c = np.sqrt(E/rho*1e+9) # m/s

        As = np.pi*Ds*Ds/4 # mm2

        # average stress in the specimen
        # dfP['Stress/MPa'] = 1/2*S/As*(dfP['I/MPa']+dfP['R/MPa']+dfP['T/MPa'])
        # stress going through the specimen
        self.dfP['Stress/MPa'] = S/As*(self.dfP['T/MPa'])
        self.dfP['I-R-T/MPa'] = self.dfP['I/MPa']-self.dfP['R/MPa']-self.dfP['T/MPa']
        self.dfP['dotStrain'] = c/Ls*1e+3 * 1e-9/E * (self.dfP['I/MPa']-self.dfP['R/MPa']-self.dfP['T/MPa'])*1e+6
        self.dfP['dStrain'] = df_int_ydx(self.dfP, y='dotStrain', x='Time/mus')*1e-6
        self.dfP['Strain'] = self.dfP['dStrain'].cumsum()

        self.dfP[['Time/mus', 'dotStrain', 'dStrain', 'Strain']].head()

        self.strainRate = round(self.dfP['dotStrain'].mean()/10.0)*10


        # ### d sigma / d epsilon. Specimen unloading cutting
        self.dfP['E(eps)/MPa'] = df_dydx(self.dfP, y='Stress/MPa', x='Strain')
        self.dfP['E(eps)/MPa'] = self.dfP['E(eps)/MPa'].rolling(kwargs['rm_window']).mean()
        unload = self.dfP['E(eps)/MPa'].idxmin()

        self.dfP.drop(self.dfP.iloc[unload:].index, inplace=True)

        # ### Calculating True Stress and Strain
        self.dfP['StrainTrue'] = -np.log(1-self.dfP['Strain'])
        self.dfP['StressTrue/MPa'] = self.dfP['Stress/MPa']*(1-self.dfP['Strain'])

        self.record = kwargs

    def __call__(self, **kwargs):
        '''
        This program parses data saved by new Rigol DS Oscilloscope.
        It contains raw Voltage(Time) dependences from two channels of the oscilloscope.
        '''

        self.df = pd.read_csv(
            kwargs['filename'],
            header=0,
            names = ['Time/s', 'CH1/V', 'CH2/V']
            )

        self.filter(**kwargs)

        self.shift(**kwargs)

        self.scale(**kwargs)

        self.syncronise(**kwargs)

        self.mechanics(**kwargs)

        # ### Printing to terminal some info at the end of preprocessing
        # ### To calm down the nerves
        if '№' in kwargs:
            prnt(kwargs['№'])
        prnt(f'Strain Rate = {self.strainRate:.0f} 1/s')

        self.record = kwargs

class Sample():
    def __init__(self, **kwargs):
        
        # ### reading the experimental notes
        self.journal = pd.read_excel(kwargs['nbFilename'], header=0)

        folder_path = os.path.dirname(kwargs['nbFilename'])
        self.journal['filename'] = folder_path+r'/'+self.journal['filename']

        records = self.journal.to_dict(orient = 'records')

        # ### creating all tested specimens        
        self.specimens = [Specimen(rm_window=100,trig_start=50,**kwargs, **records[i]) for i in range(len(self.journal.index))]

        self.journal['strainRate/1//s'] = [self.specimens[i].strainRate for i in range(len(self.journal.index))]

        # ### printing the notes
        prnt()
        print(self.journal)
