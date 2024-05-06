# %%[sec_1]
from tespy.networks import Network

# create a network object with R134a as fluid
my_plant = Network()
my_plant.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg')
# %%[sec_2]
from tespy.components import (
    CycleCloser, Pump, Condenser, Turbine, HeatExchanger, Source, Sink
)

cc = CycleCloser('cycle closer')
sg = HeatExchanger('steam generator')
mc = Condenser('main condenser')
tu = Turbine('steam turbine')
fp = Pump('feed pump')

cwso = Source('cooling water source')
cwsi = Sink('cooling water sink')
stso = Source('steam source')
stsi = Sink('steam sink')

from tespy.connections import Connection

c1 = Connection(cc, 'out1', tu, 'in1', label='1')
c2 = Connection(tu, 'out1', mc, 'in1', label='2')
c3 = Connection(mc, 'out1', fp, 'in1', label='3')
c4 = Connection(fp, 'out1', sg, 'in1', label='4')
c0 = Connection(sg, 'out1', cc, 'in1', label='0')

my_plant.add_conns(c1, c2, c3, c4, c0)

c11 = Connection(cwso, 'out1', mc, 'in2', label='11')
c12 = Connection(mc, 'out2', cwsi, 'in1', label='12')
c21 = Connection(stso, 'out1', sg, 'in2', label='21')
c22 = Connection(sg, 'out2', stsi, 'in1', label='22')

my_plant.add_conns(c11, c12)
my_plant.add_conns(c21, c22)

# %%[sec_3]
# Setting component and connection attributes
mc.set_attr(pr1=0.98, pr2=1) # Setting pressure ratios for main condenser
sg.set_attr(pr1=0.98, pr2=1) # Setting pressure ratios for steam generator
tu.set_attr(eta_s=0.9) # Setting isentropic efficiency for steam turbine
fp.set_attr(eta_s=0.75) # Setting isentropic efficiency for feed pump

c11.set_attr(T=20, p=1.2, fluid={'water': 1})
c12.set_attr(T=25)
c21.set_attr(T=150, p=2.0, fluid={'water': 1})
c22.set_attr(T=100)
c1.set_attr(T=90, p=30, m=10, fluid={'R1234yf': 1})
c2.set_attr(p=7)

# Function to run ORC model and calculate results
def run_orc_model():
    # Solve the network in design mode and print results
    my_plant.solve(mode='design')
    my_plant.print_results()
    # Initializing dictionary to store results
    result_dict = {}
    # Updating results dictionary with plotting data for components
    result_dict.update(
        {cp.label: cp.get_plotting_data()[1] for cp in my_plant.comps['object']
         if cp.get_plotting_data() is not None})
    # Returning the results dictionary
    return result_dict 

# Running the ORC model and calculating results
tespy_results = run_orc_model()

# Importing necessary libraries 
from fluprodia import FluidPropertyDiagram
import matplotlib.pyplot as plt
import numpy as np

# Creating a fluid property diagram for R1234yf
diagram = FluidPropertyDiagram('R1234yf')
# Setting unit system for the diagram
diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')

# Calculating and plotting T-s diagram
# Iterate over the results obtained from TESPy simulation
for key, data in tespy_results.items():
   # Calculate individual isolines for T-s diagram
   tespy_results[key]['datapoints'] = diagram.calc_individual_isoline(**data)

# Create a figure and axis for plotting T-s diagram
fig, ax = plt.subplots(1, figsize=(20, 10))
mydata = {
    'Q': {'values': np.linspace(0, 1, 2)},
    'T': {
        'values': np.arange(-25, 150, 25),
        'style': {'color': '#000000'}
    },
    'v': {'values': np.array([])}
}

# Set isolines for T-s diagram
diagram.set_isolines(T=mydata["T"]["values"], Q=mydata["Q"]["values"], v=mydata["v"]["values"])
diagram.calc_isolines()

# Draw isolines on the T-s diagram
diagram.draw_isolines(fig, ax, 'Ts', x_min=900, x_max=1800, y_min=0, y_max=125)

# Plot T-s curves for each component
for key in tespy_results.keys():
    datapoints = tespy_results[key]['datapoints']
    _ = ax.plot(datapoints['s'], datapoints['T'], color='#ff0000')
    _ = ax.scatter(datapoints['s'][0], datapoints['T'][0], color='#ff0000')

# Set labels and title for the T-s diagram
ax.set_xlabel('Entropy, s [J/kg.K]', fontsize=14)
ax.set_ylabel('Temperature, T [K]', fontsize=14)
ax.set_title('T-s Diagram for ORC System', fontsize=18)
plt.tight_layout()

# Save the T-s diagram plot as an SVG file
fig.savefig('Ts_fyp.svg')

# %%[sec_5]
from tespy.connections import Bus

powergen = Bus("electrical power output")

powergen.add_comps(
    {"comp": tu, "char": 0.97, "base": "component"},
    {"comp": fp, "char": 0.97, "base": "bus"},
)

my_plant.add_busses(powergen)

my_plant.solve(mode='design')
my_plant.print_results()
my_plant.save("Validation_result")

# Parametric Study and Plotting
my_plant.set_attr(iterinfo=False)
# Set electrical power attribute to None for parametric study
powergen.set_attr(P=None)

# Set font size for plots
plt.rc('font', **{'size': 18})

# Define parameter ranges for the parametric study
data = {
    'm_workingfluid': np.linspace(10, 60, 6),
    'P_boiler': np.linspace(20, 30, 6),
    'P_condenser': np.linspace(7, 17, 6),
    'm_coolingfluid': np.linspace(20, 70, 6),
}
# Initialize dictionaries to store efficiency and power values for each parameter
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

# Perform parametric study for each parameter
# 1. Varying working fluid flow rate
for M in data['m_workingfluid']:
    c1.set_attr(m=M)
    my_plant.solve('design')
    eta['m_workingfluid'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['m_workingfluid'] += [abs(powergen.P.val) / 1e3]

# Reset working fluid flow rate to base value
c1.set_attr(m=10)

# 2. Varying boiler pressure 
for P in data['P_boiler']:
    c1.set_attr(p=P)
    my_plant.solve('design')
    eta['P_boiler'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['P_boiler'] += [abs(powergen.P.val) / 1e3]

# Reset boiler pressure to base value
c1.set_attr(p=30)

# 3. Varying condenser pressure
for P in data['P_condenser']:
    c2.set_attr(p=P)
    my_plant.solve('design')
    eta['P_condenser'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['P_condenser'] += [abs(powergen.P.val) / 1e3]

# Reset condenser pressure to base value
c2.set_attr(p=7)

# 4. Varying cooling fluid flow rate
c12.set_attr(T=None)
for M in data['m_coolingfluid']:
    c11.set_attr(m=M)
    my_plant.solve('design')
    eta['m_coolingfluid'] += [abs(powergen.P.val) / sg.Q.val * 100]
    power['m_coolingfluid'] += [abs(powergen.P.val) / 1e3]

# Reset cooling fluid flow rate to base condition
c12.set_attr(T=25)
c11.set_attr(m=None)

# Create subplots for efficiency and power variation with each parameter
fig, ax = plt.subplots(2, 4, figsize=(25, 12.5), sharex='col', sharey='row')
ax = ax.flatten()
[a.grid() for a in ax]

# Plot efficiency and power for each parameter
i = 0
for key in data:
    ax[i].scatter(data[key], eta[key], s=100, color="#1f567d")
    ax[i].plot(data[key], eta[key], color="#1f567d")
    ax[i + 4].scatter(data[key], power[key], s=100, color="#18a999")
    ax[i + 4].plot(data[key], power[key], color="#18a999")
    i += 1

# Set labels and title for the subplots
ax[0].set_ylabel('Efficiency (%)')
ax[4].set_ylabel('Power (kW)')
ax[4].set_xlabel('Working Fluid Flow Rate (kg/s)')
ax[5].set_xlabel('Boiler Pressure (bar)')
ax[6].set_xlabel('Condenser Pressure (bar)')
ax[7].set_xlabel('Cooling Fluid Flow Rate (kg/s)')
plt.tight_layout()

# Save the combined plot as an SVG file
fig.savefig('fyp_rankine.svg')
plt.close()