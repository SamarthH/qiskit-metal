from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core.base import QComponent


class Airbridge_forGDS(QComponent):
    """
    The base "Airbridge" inherits the "QComponent" class.
    
    NOTE TO USER: This component is designed for GDS export only. 
    This QComponent should NOT be rendered for EM simulation.
    
    Default Options:
        * crossover_length: '22um' -- Distance between the two outer squares (aka bridge length).
                                      Usually, this should be the same length as (cpw_width + 2 * cpw_gap)
        * inner_length: '8um' -- Length of inner square. Equal to bridge width
        * outer_buffer: '3um' -- Buffer on top of inner squares and bridge for the outer rectangle
        * square_layer: 30 -- GDS layer of inner squares.
        * bridge_layer: 31 -- GDS layer of bridge.
        * outer_layer: 32 -- GDS layer of outer bridge.
    """

    # Default drawing options
    default_options = Dict(crossover_length='22um',
                           inner_length='8um',
                           outer_buffer='3um',
                           square_layer=30,
                           bridge_layer=31,
                           outer_layer =32)
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='airbridge')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""
        # Parse options
        p = self.parse_options()
        crossover_length = p.crossover_length
        bridge_width = p.inner_length
        inner_length = p.inner_length
        outer_buffer = p.outer_buffer
        # Make the inner square structure
        left_inside = draw.rectangle(inner_length, inner_length, 0, 0)
        right_inside = draw.translate(left_inside,
                                      crossover_length / 2 + inner_length / 2,
                                      0)
        left_inside = draw.translate(left_inside,
                                     -(crossover_length / 2 + inner_length / 2),
                                     0)

        inside_struct = draw.union(left_inside, right_inside)

        # Make the outer square structure
        outside_struct = draw.rectangle(crossover_length+2*inner_length+2*outer_buffer, bridge_width+2*outer_buffer, 0, 0)

        # Make the bridge structure
        bridge_struct = draw.rectangle(crossover_length+2*inner_length, bridge_width, 0, 0)

        ### Final adjustments to allow repositioning
        final_design = [bridge_struct, inside_struct, outside_struct]
        final_design = draw.rotate(final_design, p.orientation, origin=(0, 0))
        final_design = draw.translate(final_design, p.pos_x, p.pos_y)
        bridge_struct, inside_struct, outside_struct = final_design

        ### Add everything as a QGeometry
        self.add_qgeometry('poly', {'bridge_struct': bridge_struct},
                           layer=p.bridge_layer,
                           subtract=False)
        self.add_qgeometry('poly', {'inside_struct': inside_struct},
                           layer=p.square_layer,
                           subtract=False)
        self.add_qgeometry('poly', {'outside_struct': outside_struct},
                           layer=p.outer_layer,
                           subtract=False)
