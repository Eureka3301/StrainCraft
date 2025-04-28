import pandas as pd
import numpy as np
from processing import preprocessing
from processing import pulses
from processing import ultimateStress_dotEpsilon
import matplotlib.pyplot as plt
import pwlf
import seaborn as sns
from sklearn.metrics import r2_score

def pieceW(tau, dotstrain, E, sigmacrit):
    B = (2*sigmacrit)/(E*tau)
    sigmad = np.ones(np.size(dotstrain))

    for i in range(np.size(dotstrain)):
        if dotstrain[i]<=B:
            sigmad[i] = sigmacrit + tau*0.5*E*dotstrain[i]
        elif dotstrain[i]>B:
            sigmad[i] = np.sqrt(2*sigmacrit*tau*E*dotstrain[i])

    return sigmad

first = 2
last = 9
filenames = [r'D:\python\pythonProject\SHPB\MgCa_24.04\MgCa%d.csv' % i for i in range(first, last+1)]


sigma = np.empty(np.size(filenames)+1)
dotEps = np.empty(np.size(filenames)+1)

for i in range(np.size(filenames)):
    #получаем данные
    df = preprocessing(filenames[i],i, r'D:\python\pythonProject\SHPB\MgCa_linear\Voltage_MgCa.csv')

    dfP, strainRate = pulses(df, 8e-3,8)

    dotEps[i] = strainRate

    dfP1 = dfP.copy()
    dfP1 = dfP1[dfP1['Time/mus']<=30]
    #print(dfP1)
    plt.clf()

    #приближаем кусочно линейной функцией
    # initialize piecewise linear fit with your x and y data
    my_pwlf = pwlf.PiecewiseLinFit(dfP1['Time/mus'], dfP1['StressTrue/MPa'])

    # fit the data for four line segments
    res = my_pwlf.fit(2)

    # predict for the determined points
    xHat = np.linspace(min(dfP1['Time/mus']), max(dfP1['Time/mus']), num=2000)
    yHat = my_pwlf.predict(xHat)

    #определяем углы наклона и константу b (y=mx+b) (нам нужна только первая и вторая)
    m = my_pwlf.calc_slopes()
    b = my_pwlf.intercepts

    #находим точку пересечения первых двух линий
    y_intersection = (b[0]*m[1]-b[1]*m[0])/(m[1]-m[0])
    x_intersection = (b[1]-b[0])/(m[0]-m[1])

    sigma[i] = y_intersection

    #print(y_intersection, x_intersection)
    # plot the results
    sns.set_style("whitegrid")
    plt.xlabel('Время, мкс', loc='center')
    plt.ylabel('Напряжение истинное, МПа', loc='center')
    #plt.plot(dfP['Time/mus'], dfP['StressTrue/MPa'])


    sns.lineplot(data=dfP,
                 x='Time/mus',
                 y='StressTrue/MPa',
                 label='Скорость деформации: %.f 1/s' % strainRate, )


    #plt.plot(xHat, yHat, '-.')
    sns.lineplot(
                 x=xHat,
                 y=yHat,
                 label='Предел текучести: %8.2f 1/s' % y_intersection, linestyle='-.' )
    #plt.text(100,100 , 'Скорость деформации = '+str(round(strainRate,0)))
    #plt.text(100, 90, 'Критическое напряжение = ' + str(round(y_intersection, 2)))
    #plt.show()

    plt.savefig(r'D:\python\pythonProject\SHPB\MgCa_linear\MgCa_stress%d.png' % i)
sigma[0] = 220
sigma[7] = 275
sigma[8] =  200

Tau =7e-6
sigma = np.round(sigma,0)
dotEps = np.round(dotEps,0)
dotEps[8] = 1.2e-4

dotarr = np.arange(0, 2300, 1)
dotarr[0] = 1.2e-4

curvearr = pieceW(Tau,dotarr,44200,200)

y_true = sigma
y_pred = pieceW(Tau, dotEps, 44200, 200)
R2 = r2_score(y_true, y_pred)

'''for i in range(50):
    y_true = sigma
    tau = 4e-6 + 1e-7*i
    y_pred = pieceW(tau, dotEps, 44200, 200)
    print(r2_score(y_true, y_pred), tau)'''

DotEps_sigma = pd.DataFrame({
    'dotEps': dotEps,  # Первый столбец
    'sigma': sigma   # Второй столбец
})

#DotEps_sigma.to_csv(r'D:\python\pythonProject\SHPB\MgCaDotEps_sigma.csv', index = False, header=False)

plt.clf()
plt.figure(figsize=[12,4])
plt.subplot(1, 2, 1)
plt.xscale('log')
plt.xlabel('скорость деформации, 1/с', loc = 'center')
plt.ylabel('Напряжение ист., МПа', loc = 'center')

sns.scatterplot(x=dotEps, y=sigma, label='Эксперимент MgCa')
sns.lineplot(
                 x=dotarr,
                 y=curvearr,
                 label='Приближение c $\\tau =$'+str(Tau*1e6)+'мкс' + '\n $R^2$ = %6.4f' % R2, linestyle='-.', c='r' )

plt.subplot(1, 2, 2)
sigma1 = np.delete(sigma,8)

dotEps1 = np.delete(dotEps,8)


dotarr1 = np.arange(100, 2000, 1)
curvearr1 = pieceW(Tau,dotarr1,44200,200)
y_true1 = sigma1
y_pred1 = pieceW(Tau, dotEps1, 44200, 200)

plt.xscale('linear')
plt.xlabel('скорость деформации, 1/с', loc = 'center')
plt.ylabel('Напряжение ист., МПа', loc = 'center')

sns.scatterplot(x=dotEps1, y=sigma1,)
sns.lineplot(
                 x=dotarr1,
                 y=curvearr1,
                  linestyle='-.', c='r' )

plt.show()