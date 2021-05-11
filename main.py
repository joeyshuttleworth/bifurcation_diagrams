import pandas as pd
import numpy as np
import myokit
import matplotlib.pyplot as plt
import re

def run_from_states(steady_state_file, mmt_file, gkr_scales):
    # Get model and protocol, create simulation
    m, p, x = myokit.load(mmt_file)

    df = pd.read_csv(steady_state_file, delim_whitespace=True)

    list_of_var_names = [var.qname() for var in m.variables()]

    state_string=""
    for column in df.columns:
        myokit_state_name = re.sub(r'__', r'.', column)
        value = df[column].values[0]
        if(not myokit_state_name in list_of_var_names):
            print("missing")
            Exception("missing a variable")
        else:
            state_string = state_string+"{} = {}\n".format(myokit_state_name, df[column].values[0])

    original_max_gkr = m.get("IKr.gKr_max").eval()

    apds=[]

    m.set_state(m.map_to_state(state_string))

    state = m.state()
    for gkr_scale in gkr_scales:
        # Set maximal GKr
        m.set_value("IKr.gKr_max", original_max_gkr*gkr_scale)
        m.set_state(state)
        s = myokit.Simulation(m, p)
        s.set_tolerance(1e-8, 1e-8)

        var = 'membrane.Vm'
        vt = 0.9 * m.get('membrane.Vm').eval()

        s.pre(1000*500)
        d = s.run(1000)

        state=m.state()

        # Get APD
        apd=d.apd("membrane.Vm",  vt)['duration'][0]
        print(apd, gkr_scale)
        apds.append(apd)
    return gkr_scales, apds

if __name__ == "__main__":
    gkr_scales1 = np.concatenate([np.linspace(0.75, 0.6, 10), np.linspace(0.6, 0.525, 100), np.linspace(0.525, 0.35, 20)])
    res1 = run_from_states("decker_no_EAD_steadystate.dat", "decker_2009_analytic_voltage.mmt", gkr_scales1)

    gkr_scales2 = np.concatenate([np.linspace(0.35, 0.425, 10), np.linspace(0.425, 0.5, 100), np.linspace(0.5, 0.75, 25), ])
    res2 = run_from_states("decker_EAD_steadystate.dat", "decker_2009_analytic_voltage.mmt", gkr_scales2)

    plt.plot(res1[0], res1[1], label="initially using EAD steady state")
    plt.plot(res2[0], res2[1],  label="initially using steady state with no EAD")
    plt.xlabel("maximal gkr scaling factor")
    plt.ylabel("apd /ms")
    plt.legend()

    plt.show()

