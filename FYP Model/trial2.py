# Second Trial (boiler as simple heat exchanger)
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
sg = Condenser('boiler')
mc = Condenser('main condenser')
tu = Turbine('steam turbine')
fp = Pump('feed pump')

cwso = Source('cooling water source')
cwsi = Sink('cooling water sink')
stso = Source('steam source')
stsi = Sink('steam sink')

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
c21 = Connection(stso, 'out1', sg, 'in2', label='21')
c22 = Connection(sg, 'out2', stsi, 'in1', label='22')

my_plant.add_conns(c11, c12, c21, c22)
# %%[sec_3]
# Set component and connection attributes
mc.set_attr(pr1=1, pr2=0.98)
sg.set_attr(pr1=1, pr2=0.98)
tu.set_attr(eta_s=0.9)
fp.set_attr(eta_s=0.75)

c11.set_attr(T=25, m=40, fluid={'water': 1})
c21.set_attr(T=150, m=30, p=2, fluid={'water': 1})
c1.set_attr(p=30, m=10, T=120, fluid={'R1234yf': 1})
c2.set_attr(p=3)

# Solve and print results
my_plant.solve(mode='design')
my_plant.print_results()
