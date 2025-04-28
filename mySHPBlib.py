# ### Used Modules:
print('loading standard modules')
# ### working with system
import os
# ### working with data
import pandas as pd
# ### optimised math
import numpy as np
# ### property files
import json
# ### graphics
import matplotlib.pyplot as plt
import seaborn as sns
# ### filters
from scipy.signal import butter, filtfilt
print('standard modules loaded')

# ### custom print function
def prnt(s = ''):
    print('=' * os.get_terminal_size().columns)
    print(s)

# ### the object of specimen tested
class specimen():
    '''
    contains all info about single specimen tested
    '''
    def __df_dydx(self, df, x, y):
        '''
        calculates the derivative of y variable over x variable in the dataframe df
        '''
        return (df[y].shift(-1) - df[y])/(df[x].shift(-1) - df[x])

    def __df_int_ydx(self, df, x, y):
        '''
        calculates the Barrow integral (starting from the first x in dataframe.
        x values must be sorted) of y variable over x variable in the dataframe df
        with trapezoid method
        '''
        return (df[y].shift(-1)+df[y])/2*(df[x].shift(-1)-df[x])

    def __filt(self, x, y, kind, rm_window, **kwargs):
        if kind == 'rm': 
            return y.rolling(rm_window).mean()
        
        elif kind == 'lowpass':
            # === Параметры ===
            cutoff_freq = 200e+3     # Частота среза в Гц
            sampling_rate = 2/(x[1]-x[0])   # Частота дискретизации в Гц
            filter_order = 4         # Порядок фильтра

            # === Загрузка данных ===
            time = x
            signal = y

            # === Функция для создания низкочастотного фильтра ===
            def lowpass_filter(data, cutoff, fs, order=4):
                nyq = 0.5 * fs  # Частота Найквиста
                normal_cutoff = cutoff / nyq
                b, a = butter(order, normal_cutoff, btype='low', analog=False)
                filtered_signal = filtfilt(b, a, data)
                return filtered_signal

            # === Применение фильтра ===
            filtered_signal = lowpass_filter(signal, cutoff_freq, sampling_rate, filter_order)

            return filtered_signal
        
    def __init__(self,
                 filename=None,
                 dfP = None,
                 rm_window = 10,
                 trig_start = 10, # mu s
                 zero_coef = 0.6,
                 **kwargs,
                 ):
        
        '''
        This program parses data saved by Rigol DS Oscilloscope.
        It contains raw Voltage(Time) dependences from two channels of the oscilloscope.
        All it needs is 
        '''

        if filename:
            self.filename = filename
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
            df['CH1/V/filt'] = self.__filt(df['Time/s'], df['CH1/V'], kind='lowpass', rm_window=rm_window, **kwargs)
            df['CH2/V/filt'] = self.__filt(df['Time/s'], df['CH2/V'], kind='lowpass', rm_window=rm_window, **kwargs)

            #df['CH1/V/filt'] = self.__filt(df['Time/s'], df['CH1/V/filt'], kind='rm', rm_window=rm_window, **kwargs)
            #df['CH2/V/filt'] = self.__filt(df['Time/s'], df['CH2/V/filt'], kind='rm', rm_window=rm_window, **kwargs)

            # ### CH1/V/zero & CH2V/zero ### balancing the bridges
            CH1_zero = df[df['Time/mus'].between(left=0, right=trig_start)]['CH1/V/rm'].mean()
            df['CH1/V/zero'] = df['CH1/V/filt'] - CH1_zero

            CH2_zero = df[df['Time/mus'].between(left=0, right=trig_start)]['CH2/V/rm'].mean()
            df['CH2/V/zero'] = df['CH2/V/filt'] - CH2_zero


            # ### Voltage on bridges to stress in the bars 
            # Let $\sigma = K \cdot V$
            K = kwargs['K/MPa//mV'] # MPa/mV
            V0 = kwargs['V0/V'] # V

            # bars diameter
            d = kwargs['d/mm'] # mm
            S = np.pi*d*d/4 # mm2

            # bars mechanical properties
            rho = kwargs['rho/kg//m3'] # kg/m3
            E = kwargs['E/GPa'] # GPa

            # ### Input voltage on WB
            V1 = kwargs['V0_CH1/V'] # V
            V2 = kwargs['V0_CH2/V'] # V

            # ### The stress and strain pulses in the bars
            df['CH1/MPa'] = df['CH1/V/zero'] * K*1e+3 * V1/V0
            df['CH2/MPa'] = df['CH2/V/zero'] * K*1e+3 * V2/V0

            df['CH1/strain'] = df['CH1/MPa'] / E *1e-3
            df['CH2/strain'] = df['CH2/MPa'] / E * 1e-3

            # ### start of incident, transmitted, reflected pulses
            # We find the beginning of the incident pulse by the prevailing of "zero" level (noiseZero MPa).
            noiseZero = zero_coef*K # MPa

            i_start = df[df['CH1/MPa'] > noiseZero].index[0]


            # The shift to syncronise gauges is evaluated by their position on bars.
            # As we have time grid inherited from the discretisation of the oscilloscope
            # the shift will be produced according to it.
            c = np.sqrt(E/rho*1e+9) # m/s
            L1 = kwargs['L1/m'] # m
            L2 = kwargs['L2/m'] # m

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

            striker = kwargs['striker/m'] # m
            T = 2*striker / c * 1e+6 # mus

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

            dfP['I+R/MPa'] = dfP['I/MPa'] + dfP['R/MPa']


            # ### Stress(t) and Strain(t)
            Hs = kwargs['H_s/mm'] # mm
            Ds = kwargs['D_s/mm'] # mm

            As = np.pi*Ds*Ds/4 # mm2

            # average stress in the specimen
            # dfP['Stress/MPa'] = 1/2*S/As*(dfP['I/MPa']+dfP['R/MPa']+dfP['T/MPa'])
            # stress going through the specimen
            dfP['Stress/MPa'] = S/As*(dfP['T/MPa'])
            dfP['I-R-T/MPa'] = dfP['I/MPa']-dfP['R/MPa']-dfP['T/MPa']

            dfP['dotStrain'] = c/Hs*1e+3 * 1e-9/E * (dfP['I/MPa']-dfP['R/MPa']-dfP['T/MPa'])*1e+6
            dfP['dStrain'] = self.__df_int_ydx(dfP, y='dotStrain', x='Time/mus')*1e-6
            dfP['Strain'] = dfP['dStrain'].cumsum()

            dfP[['Time/mus', 'dotStrain', 'dStrain', 'Strain']].head()

            self.strainRate = round(dfP['dotStrain'].mean()/10.0)*10


            # ### d sigma / d epsilon. Specimen unloading cutting
            dfP['E(eps)/MPa'] = self.__df_dydx(dfP, y='Stress/MPa', x='Strain')
            dfP['E(eps)/MPa'] = dfP['E(eps)/MPa'].rolling(rm_window).mean()
            unload = dfP['E(eps)/MPa'].idxmin()

            dfP.drop(dfP.iloc[unload:].index, inplace=True)

            # ### Calculating True Stress and Strain
            dfP['StrainTrue'] = -np.log(1-dfP['Strain'])
            dfP['StressTrue/MPa'] = dfP['Stress/MPa']*(1-dfP['Strain'])

            # ### Saving all the info we may need
            self.dfP = dfP[['Time/mus', 'I/MPa', 'R/MPa', 'T/MPa', 'I+R/MPa', 'dotStrain', 'Strain', 'Stress/MPa', 'StrainTrue', 'StressTrue/MPa']]

            # ### Printing to terminal some info at the end of preprocessing
            # ### To calm down the nerves
            if '№' in kwargs:
                prnt(kwargs['№'])
            if 'v/m//s' in kwargs:
                self.v = kwargs['v/m//s']
            prnt(f'K = {K} MPa/mV, striker length = {striker} m, impact velocity = {self.v} m/s')
            prnt(f'Strain Rate = {self.strainRate:.0f} 1/s')
        elif dfP:
            self.dfP = dfP
    
    def plot_balance(self):
        sns.lineplot(data=self.dfP,
                     x='Time/mus',
                     y='I/MPa',
                     label = 'I'
                     )
        sns.lineplot(data=self.dfP,
                     x='Time/mus',
                     y='R/MPa',
                     label = 'R'
                     )
        sns.lineplot(data=self.dfP,
                     x='Time/mus',
                     y='T/MPa',
                     label = 'T'
                     )
        sns.lineplot(data=self.dfP,
                     x='Time/mus',
                     y='I+R/MPa',
                     label = 'I+R'
                     )
        plt.show()


# ### the object of several specimens
class sample():
    # ### creating sample based on one serie
    def __init__(self,
                 wrkdir,
                 nbFilename,
                 propFilename,
                 ):
        # ### collecting info about used files 
        self.wrkdirs = [wrkdir]
        self.nbFilenames = [nbFilename]
        self.propFilenames = [propFilename]

        # ### uploading json property file of the setup
        with open(propFilename, 'r') as file:
            properties = json.load(file)

        # ### enter the serie dir
        cwd = os.getcwd()
        os.chdir(wrkdir)

        # ### reading the experimental notes
        self.nb = pd.read_excel(nbFilename, header=0)

        # ### creating all tested specimens
        self.specimens = []
        for record in self.nb.to_dict(orient = 'records'):
            self.specimens.append(specimen(**properties, **record))

        self.nb['StrainRate/1//s'] = np.array([self.specimens[i].strainRate for i in range(len(self.specimens))])

        # ### return to the program dir
        os.chdir(cwd)
    
    # ### adding new series by calling the object
    def __call__(self,
                 wrkdir,
                 nbFilename,
                 propFilename,
                 ):
        # ### collecting info about used files 
        self.wrkdirs.append(wrkdir)
        self.nbFilenames.append(nbFilename)
        self.propFilenames.append(propFilename)

        # ### uploading json property file of the setup
        with open(propFilename, 'r') as file:
            properties = json.load(file)

        # ### enter the serie dir
        cwd = os.getcwd()
        os.chdir(wrkdir)

        # ### reading and adding the experimental notes
        nb = pd.read_excel(nbFilename, header=0)
        self.nb = pd.concat([self.nb, nb])

        # ### creating all tested specimens
        for record in nb.to_dict(orient = 'records'):
            self.specimens.append(specimen(**properties, **record))

        # ### return to the program dir
        os.chdir(cwd)