# StrainCraft
This is a small program that deals with raw data from the Rigol DS oscilloscope recording signals from the wheatstone bridges on the SHPB.

---

## mySHPBlib.py
It is the heart of the program. It contains the class **specimen** that corresponds to one tested specimen.
The class can be constructed through file of oscilloscope.
(but there is an option to load syncronised pulses **dfP**)

---

## notebook.xlsx and rawdata.csv and properties.json

The crucial columns in *notebook.xlsx* are as follows.

| H_s/mm | v/m//s | striker/m | filename |
| ---    | ---    | ---       | ---      |
| 5      | 5.6    | 0.6       | Al.csv   |

The each *rawdata.csv* file contains three columns.

| Time(s) | CH1(V) | CH2(V) |
| ---     | ---    | ---    |
| 0.0000  | 0.0000 | 0.0000 |

The *properties.json* contains record of bars parameters that stays mostly permanent.

| parameter | description                                       |
|---        |---                                                |
|K/MPa//mV  | sensitivity of WB                                 |
|d/mm       |bars diameter                                      |
|rho/kg//m3 |bars density                                       |
|E/GPa      | bars Young modulus                                |
|nu         | bars Poisson's ration                             |
|L1/m       | distance from the end of the rod to the first WB  |
|L1/m       | distance from the end of the rod to the second WB |

