#!/usr/bin/env python3

import os
import argparse
import pandas as pd
import numpy as np
import myokit
import matplotlib.pyplot as plt
import re

def run_from_states(steady_state_file, mmt_file, period=1000, block=0, pre_paces=100):
    # Oxmeta tag for the gkr_variable
    gkr_var_meta = "membrane_rapid_delayed_rectifier_potassium_current_conductance"

    # Get model and protocol, create simulation
    m, p, x = myokit.load(mmt_file)

    # Get gkr var label
    gkr_var_label=""
    # Get gkr variable
    for var in m.variables(deep=True):
        if 'oxmeta' in var.meta:
            if var.meta['oxmeta'] == gkr_var_meta:
                gkr_var_label = var.qname()
                break
    print(gkr_var_label)

    original_max_gkr = m.get(gkr_var_label).eval()
    gkr_value =  original_max_gkr*(1-block)

    # Get qname for voltage
    voltage_qname = next(filter(lambda var: var.meta['oxmeta']=="analytic_voltage" if 'oxmeta' in var.meta else False, m.variables()))

    if steady_state_file != "" and steady_state_file is not None:
        df = pd.read_csv(steady_state_file, delim_whitespace=True)
        list_of_var_names = [var.qname() for var in m.variables()]
        state_string=""
        for column in df.columns:
            myokit_state_name = re.sub(r'__', r'.', column)
            value = df[column].values[0]
            if myokit_state_name in list_of_var_names:
                state_string = state_string+"{} = {}\n".format(myokit_state_name, df[column].values[0])
            else:
                # search oxmeta labels
                qname = next(filter(lambda var: var.meta['oxmeta']==column if 'oxmeta' in var.meta else False, m.variables()), "")
                if qname == "":
                    Exception("Coudln't find variable, {} in {}".format(column, mmt_file))
                else:
                    state_string = state_string + "{} = {}\n".format(qname, df[column].values[0])
        m.set_state(m.map_to_state(state_string))

    m.set_value(gkr_var_label, gkr_value)
    # Set protocol
    duration = p.head().duration()
    level    = p.head().level()*2
    new_p = myokit.pacing.blocktrain(period, duration, level=level)
    p = new_p

    s = myokit.Simulation(m, p)

    # Set tolerances to be the same as the Chaste code
    s.set_tolerance(1e-08, 1e-08)

    vt = 0.9 * m.get(voltage_qname).eval()

    s.pre(period*pre_paces)
    d = s.run(5000*period)

    state=m.state()

    # Get APD
    apds=d.apd(voltage_qname,  vt)['duration']
    return apds, s

def make_plot(mmt_file, steady_state_files, period=1000, block=0, output_name="or_2017_bifurcation", args=None):
    if args is not None:
        output_dir = args.output_dir
        pre_paces = args.pre_paces
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    apds1, s1 = run_from_states(steady_state_files[0], mmt_file, period, block, pre_paces)
    apds2, s2 = run_from_states(steady_state_files[1], mmt_file, period, block, pre_paces)

    print(apds1, apds2)

    plt.plot(apds1, label="initially using 'bad' initial conditions")
    plt.plot(apds2, label="initially using default initial conditions")

    plt.ylabel("apd /ms")
    plt.title("AP90 comparison")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "{}_apds.pdf".format(output_name)))
    plt.clf()

    # Compare action potentials
    d1 = s1.run(period-1)
    d2 = s2.run(period-1)
    plt.plot(np.mod(d1['environment.time'], period), d1['membrane.v'])
    plt.plot(np.mod(d2['environment.time'], period), d2['membrane.v'])
    plt.savefig(os.path.join(output_dir, output_name + "final_action_potentials.pdf"))
    plt.clf()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Show two different steady states which exists for the O'Hara Rudy 2017 model under certain conditions")
    parser.add_argument("-p", "--pre_paces", help="The number of paces to run before data logging starts", type=int, default=1000)
    parser.add_argument("-o", "--output_dir", help="The directory to output plots to", default="output", type=str)
    args = parser.parse_args()
    make_plot("ohara_2017.mmt", [None, "ohara_2017_bad.csv"], 1250, 0.5, "ohara_rudy_2017_bifurcation", args=args)

