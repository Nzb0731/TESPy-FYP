# Importing necessary libraries 
from fluprodia import FluidPropertyDiagram
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Importing TESPy libraries for defining ORC components and connections
from tespy.networks import Network
from tespy.components import (CycleCloser, Pump, Condenser, Turbine, HeatExchanger, Source, Sink)
from tespy.connections import Connection

# Creating a fluid property diagram for R1234yf
diagram = FluidPropertyDiagram('R1234yf')
# Setting unit system for the diagram
diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')

# Creating a TESPy network object
my_plant = Network()
# Setting unit system for the network
my_plant.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg')
# Disabling iteration information display during solving
my_plant.set_attr(iterinfo=False)

# Defining components and connections for the ORC system
cc = CycleCloser('Cycle Closer')
sg = HeatExchanger('Evaporator')
mc = Condenser('Condenser')
tu = Turbine('Turbine')
fp = Pump('Pump')

cwso = Source('CW Source')
cwsi = Sink('CW Sink')
stso = Source('Steam Source')
stsi = Sink('Steam Sink')

# Creating connections between components
c1 = Connection(cc, 'out1', tu, 'in1', label='1') # Connection from cycle closer to steam turbine
c2 = Connection(tu, 'out1', mc, 'in1', label='2') # Connection from steam turbine to main condenser
c3 = Connection(mc, 'out1', fp, 'in1', label='3') # Connection from main condenser to feed pump  
c4 = Connection(fp, 'out1', sg, 'in1', label='4') # Connection from feed pump to steam generator
c0 = Connection(sg, 'out1', cc, 'in1', label='0') # Connection from steam generator to cycle closer

c11 = Connection(cwso, 'out1', mc, 'in2', label='11')
c12 = Connection(mc, 'out2', cwsi, 'in1', label='12')
c21 = Connection(stso, 'out1', sg, 'in2', label='21')
c22 = Connection(sg, 'out2', stsi, 'in1', label='22')

# Adding connections to the network
my_plant.add_conns(c1, c2, c3, c4, c0) # Adding primary connections
my_plant.add_conns(c11, c12, c21, c22) # Adding secondary connections

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

# Assess Electrical Power
from tespy.connections import Bus

# Create a bus for electrical power output
powergen = Bus("electrical power output")

# Add components to the bus for power generation
powergen.add_comps(
    {"comp": tu, "char": 1, "base": "component"},
    {"comp": fp, "char": 1, "base": "bus"},
)

# Add the power generation bus to the network
my_plant.add_busses(powergen)

# Solve the network to determine electrical power output
my_plant.solve(mode='design')
my_plant.print_results()

# Save the results in the structure of csv.files
my_plant.save("ORC_result")

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

# Create a DataFrame from the dictionaries containing the results
results_df = pd.DataFrame({'m_workingfluid': eta['m_workingfluid'],
                           'P_boiler': eta['P_boiler'],
                           'P_condenser': eta['P_condenser'],
                           'm_coolingfluid': eta['m_coolingfluid'],
                           'Power_m_workingfluid': power['m_workingfluid'],
                           'Power_P_boiler': power['P_boiler'],
                           'Power_P_condenser': power['P_condenser'],
                           'Power_m_coolingfluid': power['m_coolingfluid']})

# Export the DataFrame to a CSV file
results_df.to_csv('FYP Simulation Result.csv', index=False)

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

# Define a dictionary to map parameter keys to their corresponding x-axis labels
x_axis_labels = {
    'm_workingfluid': 'Working Fluid Flow Rate (kg/s)',
    'P_boiler': 'Boiler Pressure (bar)',
    'P_condenser': 'Condenser Pressure (bar)',
    'm_coolingfluid': 'Cooling Fluid Flow Rate (kg/s)'
}

# Create separate plots for efficiency and power variation with each parameter
for key in data:
    fig, ax = plt.subplots(1, 2, figsize=(20, 10))

    ax[0].scatter(data[key], eta[key], s=100, color="#1f567d")
    ax[0].plot(data[key], eta[key], color="#1f567d")
    ax[0].set_ylabel('Efficiency (%)')

    ax[1].scatter(data[key], power[key], s=100, color="#18a999")
    ax[1].plot(data[key], power[key], color="#18a999")
    ax[1].set_ylabel('Power (kW)')

    ax[0].set_xlabel(x_axis_labels[key])
    ax[1].set_xlabel(x_axis_labels[key])

    plt.tight_layout()

    # Save individual plots for each parameter as SVG files
    fig.savefig(f'fyp_rankine_{key}.svg')
    plt.close()
