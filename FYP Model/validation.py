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
mc.set_attr(pr1=1, pr2=0.98)
sg.set_attr(pr=0.9)
tu.set_attr(eta_s=0.9)
fp.set_attr(eta_s=0.75)

c11.set_attr(T=20, p=1.2, fluid={'water': 1})
c12.set_attr(T=30)
c1.set_attr(T=600, p=150, m=10, fluid={'R1234yf': 1})
c2.set_attr(p=0.1)

my_plant.solve(mode='design')
my_plant.print_results()

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
my_plant.save("SRC_result")