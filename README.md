# StrainCraft
This is a small program that deals with raw data from the Rigol DS oscilloscope recording signals from the wheatstone bridges on the SHPB.

* Extra calibration via striker speed can be added.

* The program classes have a big mess in positional and keyword arguments. There is a great miscellaneous in filenames, workdirs and parameters.
* Right now it is the best version I could assemble.

---

## mySHPB_lib.py
It is the heart of the program. It contains the class **specimen** that corresponds to one tested specimen.
All the processed info can be stored in this class for further consideration of this objects in whatever combinations.
For this purpose (as the specimens are mostly tested in series) the **expSeries** class is built.

---

## notebook.xlsx and rawdata.csv

There is a strict format on input files. __I will write about it later.__ :crossed_fingers:

---

## props{year}{month}.json
It contains the properties of the setup. The date in the name reflects the period it was calibrated (mainly only the bridges can change).
Actually it can be stored in the code, but the idea is to keep the lib immanent to the physical setup.

| parameter | description                                       |
|---        |---                                                |
| K/MPa//mV | sensitivity of WB                                 |
|d/mm       |bars diameter                                      |
|rho/kg//m3 |bars density                                       |
|E/GPa      | bars Young modulus                                |
|nu         | bars Poisson's ration                             |
|striker/cm | striker length                                    |
|L1/m       | distance from the end of the rod to the first WB  |
|L1/m       | distance from the end of the rod to the second WB |

## calculate.py
It is a file where one can work with the lib processing experiments conducted. :smile:
First processing of the program and dumping to pickle.bin

## debug.ipynb
Returned to calibrate the program.

## werkstat.py
Working with joint experimental series.
