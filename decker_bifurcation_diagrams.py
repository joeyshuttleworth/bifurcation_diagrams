import pandas as pd
import numpy as np
import myokit
import matplotlib.pyplot as plt
import re

def run_from_states(steady_state_file, mmt_file, gkr_scales, period=1000):
    # Oxmeta tag for the gkr_variable
    gkr_var_meta = "membrane_rapid_delayed_rectifier_potassium_current_conductance"

    # Get model and protocol, create simulation
    m, p, x = myokit.load(mmt_file)

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


    apds=[]

    state = m.state()
    gkr_var_label=""
    # Get gkr variable
    for var in m.variables(deep=True):
        if 'oxmeta' in var.meta:
            if var.meta['oxmeta'] == gkr_var_meta:
                gkr_var_label = var.qname()
                break
    print(gkr_var_label)
    # Set protocol
    duration = p.head().duration()
    level    = p.head().level()*2
    new_p = myokit.pacing.blocktrain(period, duration, level=level)
    p = new_p

    original_max_gkr = m.get(gkr_var_label).eval()
    for gkr_scale in gkr_scales:
        # Set maximal GKr
        gkr_value =  original_max_gkr*gkr_scale
        m.set_value(gkr_var_label, gkr_value)
        # m.set_state(state)
        s = myokit.Simulation(m, p)

        # Set tolerances to be the same as the Chaste code
        s.set_tolerance(1e-08, 1e-08)

        vt = 0.9 * m.get(voltage_qname).eval()

        s.pre(3000*period)
        d = s.run(period)

        state=m.state()

        # Get APD
        apd=d.apd(voltage_qname,  vt)['duration'][0]

#        plt.plot(d['environment.time'], d['membrane.v'])
        print(apds, gkr_scale, gkr_value)
        apds.append(apd)
    return gkr_scales, apds

def make_plot(mmt_file, steady_state_files, gkr_scales, output_name="output.pdf", period=1000):
    res1 = run_from_states(steady_state_files[0], mmt_file, gkr_scales[0], 1000)
    res2 = run_from_states(steady_state_files[1], mmt_file, gkr_scales[1], 1000)
    # Run from standard ICs

    print(res1, res2)

    plt.plot(res1[0], res1[1], label="initially using EAD steady state")
    plt.plot(res2[0], res2[1],  label="initially using steady state with no EAD")

    plt.xlabel("maximal gkr scaling factor")
    plt.ylabel("apd /ms")
    plt.legend()
    plt.savefig(output_name)



if __name__ == "__main__":
    # gkr_scales = np.concatenate([np.linspace(0.35, 0.425, 2), np.linspace(0.425, 0.5, 10), np.linspace(0.5, 0.75, 2), ])
    gkr_scales=np.linspace(0.5,1,2)
    make_plot("ohara_2017.mmt", [None, "ohara_2017_bad.csv"], [gkr_scales, gkr_scales], "ohara_rudy_2017 bifurcation example", 1000)

