# StrainCraft
This is a small program that deals with raw data from the Rigol DS oscilloscope recording signals from the wheatstone bridges on the SHPB.

---

## mySHPBlib.py
It is the heart of the program. It contains the class **specimen** that corresponds to one tested specimen.
The class can be constructed through file of oscilloscope.
(but there is an option to load syncronised pulses **dfP**)

All the processed info can be stored in this class for further consideration of this objects in whatever combinations.
For this purpose (as the specimens are mostly tested in series) the **journal** class is built.
The class can be constructed by reading experimental notes from notebook.
The records can be merged, dropped and whatever needed by corresponding procedures.

---

## notebook.xlsx and rawdata.csv

There is a strict format on input files. __I will write about it later.__ :crossed_fingers:
Below are the column names (with examples) that must be in notebook .xlsx file not to crash the program.

| H_s/mm | D_s/mm | v/m//s | filename |
| ---    | ---    | ---    | ---      |
| 5      | 8      | 5.6    | Al.csv   |

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

## werkstat.py
The place one makes his dreams come true.
