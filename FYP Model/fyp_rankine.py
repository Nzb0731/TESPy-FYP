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
c12.set_attr(T=30)
c1.set_attr(T=600, p=150, m=10, fluid={'water': 1})
c2.set_attr(p=0.1)

# Solve and print results
my_plant.solve(mode='design')
my_plant.print_results()
# %%[sec_4]
# Modify attributes, solve again and print results
mc.set_attr(ttd_u=4)
c2.set_attr(p=None)

my_plant.solve(mode='design')
my_plant.print_results()
# %%[sec_5]
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
# Modify Attributes for Off-Design Simulation
powergen.set_attr(P=-10e6)
c1.set_attr(m=None)

my_plant.solve(mode='design')
my_plant.print_results()
# %%[sec_7]
# Parametric Study and Plotting
my_plant.set_attr(iterinfo=False)
c1.set_attr(m=20)
powergen.set_attr(P=None)
import matplotlib.pyplot as plt
import numpy as np

# make text reasonably sized
plt.rc('font', **{'size': 18})
# Step 1: Initialization
# Step 1a: Setup arrays for different values of live steam temperature, 
# cooling water temperature, and love steam pressure.
data = {
    'T_livesteam': np.linspace(450, 750, 7),
    'T_cooling': np.linspace(15, 45, 7),
    'p_livesteam': np.linspace(75, 225, 7)
}
# Step 1b: Initialize dictionaries ('eta' and 'power') to store efficiency
# and power values.
eta = {
    'T_livesteam': [],
    'T_cooling': [],
    'p_livesteam': []
}
power = {
    'T_livesteam': [],
    'T_cooling': [],
    'p_livesteam': []
}
# Step 2: Parametric Study Loop
# Loop over live steam temperature values, set the corresponding attribute,
# solve the network in design mode, and record the efficiency and power.
for T in data['T_livesteam']:
    c1.set_attr(T=T)
    my_plant.solve('design')
    eta['T_livesteam'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['T_livesteam'] += [abs(powergen.P.val) / 1e6]

# Step 3: Reset to base temperature
# Reset the live steam temperature to the base value for the next parametric study.
c1.set_attr(T=600)

# Step 4: Repeat for Cooling Water Temperature
# Similar loops are used for varying cooling water temperature (T_cooling) 
for T in data['T_cooling']:
    c12.set_attr(T=T)
    c11.set_attr(T=T - 10)
    my_plant.solve('design')
    eta['T_cooling'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['T_cooling'] += [abs(powergen.P.val) / 1e6]

# reset to base temperature
c12.set_attr(T=30)
c11.set_attr(T=20)

# Step 5: Repeat for Live Steam Pressure
# Similar loops are used for varying live steam pressure (p_livesteam). 
for p in data['p_livesteam']:
    c1.set_attr(p=p)
    my_plant.solve('design')
    eta['p_livesteam'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['p_livesteam'] += [abs(powergen.P.val) / 1e6]

# reset to base pressure
c1.set_attr(p=150)

# Step 6: Plotting
# Plots the results of the parametric study. 
# Three plots are created for each parameter, showing the relationship between the parameter and efficiency or power.
fig, ax = plt.subplots(2, 3, figsize=(16, 8), sharex='col', sharey='row')

ax = ax.flatten()
[a.grid() for a in ax]

i = 0
for key in data:
    ax[i].scatter(data[key], eta[key], s=100, color="#1f567d")
    ax[i + 3].scatter(data[key], power[key], s=100, color="#18a999")
    i += 1

ax[0].set_ylabel('Efficiency in %')
ax[3].set_ylabel('Power in MW')
ax[3].set_xlabel('Live steam temperature in °C')
ax[4].set_xlabel('Feed water temperature in °C')
ax[5].set_xlabel('Live steam pressure in bar')
plt.tight_layout()
fig.savefig('rankine_parametric.svg')
plt.close()
# %%[sec_8]
# Set Attributions for Off-Design Simulation
# Sets specific attributes for off-design simulation. 
# For example, it sets the main condenser to be off-design with a temperature difference (ttd_u) 
# and the cooling water mass flow (v) as off-design parameters.
mc.set_attr(design=["ttd_u"], offdesign=["kA"])
c11.set_attr(offdesign=["v"])
c12.set_attr(design=["T"])
c1.set_attr(design=["p"])
tu.set_attr(offdesign=["cone"])
# %%[sec_9]
# Save the Design for Off-Design Simulation
# Solves the design case and saves it for later use in off-design simulations.
my_plant.solve("design")
my_plant.save("rankine_design")
# %%[sec_10]
# Partload Efficiency Loop
partload_efficiency = []
partload_m_range = np.linspace(20, 10, 11)

for m in partload_m_range:
    c1.set_attr(m=m)
    my_plant.solve("offdesign", design_path="rankine_design")
    partload_efficiency += [abs(powergen.P.val) / sg.Q.val * 100]

# Plotting Partload Efficiency
fig, ax = plt.subplots(1, figsize=(16, 8))
ax.grid()
ax.scatter(partload_m_range, partload_efficiency, s=100, color="#1f567d")
ax.set_xlabel("Mass flow in kg/s")
ax.set_ylabel("Plant electrical efficiency in %")

plt.tight_layout()
fig.savefig('rankine_partload.svg')
plt.close()
# %%[sec_11]