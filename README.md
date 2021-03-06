# decker_bifurcation_diagram

A demonstration of two dramatically different steady states that can exist for the same parameter sets and \Gamma0 in the decker 2009 model of canine cardiomyocytes. These plots are produced by running main.py

# ohara\_apd\_comparison
Running ohara\_apd\_comparison.py shows a subtler example where the difference in action potentials is barely noticeable but the difference in action potentials is greater than 1ms

# Running

First install a virtual environment and install the requirements. First you will need to install the requirements for myokit http://myokit.org/linux then do

``` 
python3 -m venv venv
activate venv/bin/activate
pip install -r requirements.txt
```

Then run either 
```
python3 decker_bifurcation_diagram.py
```
or 
```
python3 ohara_apd_comparison.py
```
