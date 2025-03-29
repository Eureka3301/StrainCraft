# StrainCraft
This is a small program that deals with raw data from the Rigol DS oscilloscope recording signals from the wheatstone bridges on the SHPB.

## mySHPB_lib.py
It is the heart of the program. It contains the class SHPB_test that corresponds to one tested specimen.
All the processed info can be stored in this class for further consideration of this objects in whatever combinations.

## props2025march.json
It contains the properties of the setup. The date in the name reflects the period it was calibrated (mainly only the bridges can change).
Actually it can be stored in the code, but the idea is to keep the lib immanent to the physical setup.

## main.py
It is a file where one can work with the lib processing needed experiments.
