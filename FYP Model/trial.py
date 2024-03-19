# First Trial (boiler as steam generator)
# %%[sec_1]
from tespy.networks import Network

# create a network object with R1234yf as fluid (current code is water)
my_plant = Network()
my_plant.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg')
# %%[sec_2]
# import TESPy components
from tespy.components import (
    CycleCloser, Pump, Condenser, Turbine, SimpleHeatExchanger, Source, Sink
)

# create components
cc = CycleCloser('cycle closer')
sg = SimpleHeatExchanger('steam generator')
mc = Condenser('main condenser')
tu = Turbine('steam turbine')
fp = Pump('feed pump')

cwso = Source('cooling water source')
cwsi = Sink('cooling water sink')

# Import TESPy connections
from tespy.connections import Connection

# Create connections between components
c1 = Connection(cc, 'out1', tu, 'in1', label='1')
c2 = Connection(tu, 'out1', mc, 'in1', label='2')
c3 = Connection(mc, 'out1', fp, 'in1', label='3')
c4 = Connection(fp, 'out1', sg, 'in1', label='4')
c0 = Connection(sg, 'out1', cc, 'in1', label='0')

# Add connections to the network
my_plant.add_conns(c1, c2, c3, c4, c0)

c11 = Connection(cwso, 'out1', mc, 'in2', label='11')
c12 = Connection(mc, 'out2', cwsi, 'in1', label='12')

my_plant.add_conns(c11, c12)
# %%[sec_3]
# Set component and connection attributes
mc.set_attr(pr1=1, pr2=0.98)
sg.set_attr(pr=0.9)
tu.set_attr(eta_s=0.9)
fp.set_attr(eta_s=0.75)

c11.set_attr(T=20, p=1.2, fluid={'water': 1})
c12.set_attr(T=25)
c1.set_attr(T=90, p=30, m=10, fluid={'R1234yf': 1})
c2.set_attr(p=7)

# Solve and print results
my_plant.solve(mode='design')
my_plant.print_results()

# %%[sec_4]
# Modify attributes (remove how much, replace with how much)

# %%[sec_5]
# Assess Electrical Power
from tespy.connections import Bus

# Create a Bus for Electrical Power Output
powergen = Bus("electrical power output")

# Adding components to the bus
powergen.add_comps(
    {"comp": tu, "char": 0.97, "base": "component"},
    {"comp": fp, "char": 0.97, "base": "bus"},
)

# Adding bus to the network
my_plant.add_busses(powergen)

# Solve the network
my_plant.solve(mode='design')
my_plant.print_results()

# %%[sec_6]
# Parametric Study and Plotting
my_plant.set_attr(iterinfo=False)
powergen.set_attr(P=None)
import matplotlib.pyplot as plt
import numpy as np

# make text reasonably sized
plt.rc('font', **{'size': 18})
# Step 1: Initialization
# Step 1a: Setup arrays for different values of live steam temperature, 
# cooling water temperature, and love steam pressure.
data = {
    'm_workingfluid': np.linspace(10, 60, 6),
    'P_boiler': np.linspace(20, 30, 6),
    'P_condenser': np.linspace(7, 17, 6),
    'm_coolingfluid': np.linspace(20, 70, 6),
}
# Step 1b: Initialize dictionaries ('eta' and 'power') to store efficiency
# and power values.
eta = {
    'm_workingfluid':[],
    'P_boiler': [],
    'P_condenser': [],
    'm_coolingfluid':[],
}
power = {
    'm_workingfluid':[],
    'P_boiler': [],
    'P_condenser': [],
    'm_coolingfluid':[],
}
# Step 2: Parametric Study Loop
# Loop over live steam temperature values, set the corresponding attribute,
# solve the network in design mode, and record the efficiency and power.
for M in data['m_workingfluid']:
    c1.set_attr(m=M)
    my_plant.solve('design')
    eta['m_workingfluid'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['m_workingfluid'] += [abs(powergen.P.val) / 1e6]

# Step 3: Reset to base working fluid flow rate
# Reset the working fluid flow rate to the base value for the next parametric study.
c1.set_attr(m=10)

# Step 4: Repeat for Boiler Pressure
# Similar loops are used for varying cooling water temperature (T_cooling) 
for P in data['P_boiler']:
    c1.set_attr(p=P)
    my_plant.solve('design')
    eta['P_boiler'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['P_boiler'] += [abs(powergen.P.val) / 1e6]

# reset to base boiler pressure
c1.set_attr(p=30)

# Step 5: Repeat for Condenser Pressure
# Similar loops are used for varying live steam pressure (p_livesteam). 
for P in data['P_condenser']:
    c2.set_attr(p=P)
    my_plant.solve('design')
    eta['P_condenser'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['P_condenser'] += [abs(powergen.P.val) / 1e6]

# reset to base pressure
c2.set_attr(p=7)

# Step 6: Repeat for Cooling Fluid Flow Rate
# Similar loops are used for varying live steam pressure (p_livesteam). 
c12.set_attr(T=None)
for M in data['m_coolingfluid']:
    c11.set_attr(m=M)
    my_plant.solve('design')
    eta['m_coolingfluid'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['m_coolingfluid'] += [abs(powergen.P.val) / 1e6]

# reset to base condition
c12.set_attr(T=25)

# Step 7: Plotting
# Plots the results of the parametric study. 
# Three plots are created for each parameter, showing the relationship between the parameter and efficiency or power.
fig, ax = plt.subplots(2, 4, figsize=(25, 12.5), sharex='col', sharey='row')

ax = ax.flatten()
[a.grid() for a in ax]

i = 0
for key in data:
    ax[i].scatter(data[key], eta[key], s=100, color="#1f567d")
    ax[i + 4].scatter(data[key], power[key], s=100, color="#18a999")
    i += 1

ax[0].set_ylabel('Efficiency in %')
ax[4].set_ylabel('Power in MW')
ax[4].set_xlabel('Working Fluid Flow Rate (kg/s)')
ax[5].set_xlabel('Boiler Pressure (bar)')
ax[6].set_xlabel('Condenser Pressure (bar)')
ax[7].set_xlabel('Cooling Fluid Flow Rate (kg/s)')
plt.tight_layout()
fig.savefig('trial.svg')
plt.close()