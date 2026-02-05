# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent
import numpy as np
from shapely.geometry.base import CAP_STYLE


class CoupledLineTeeCustom(QComponent):
    """Generates a two/three/four pin (+) structure comprised of a primary one/two pin CPW
    transmission line, and a secondary one/two pin neighboring CPW transmission
    line that is capacitively/inductively coupled to the primary. Such a
    structure can be used, as an example, for generating CPW resonator hangars
    off of a transmission line.

    Inherits QComponent class.

    ::
              +
              |
              |
              |
            1 ----------------+ 0
        ------------------------------+
        |
        |
        |
        |
        +

    .. image::
        CoupledLineTee.png

    .. meta::
        Coupled Line Tee

    Default Options:
        * prime_width: 'cpw_width' -- The width of the trace of the two pin CPW transmission line
        * prime_gap: 'cpw_gap' -- The dielectric gap of the two pin CPW transmission line
        * prime_length: 100um -- The length of the main part of the prime cpw
        * prime_down_length: '0um' -- The length of the hanging part of the prime cpw   
        
        * second_width: 'cpw_width' -- The width of the trace of the one pin CPW transmission line
        * second_gap: 'cpw_gap' -- The dielectric gap of the one pin CPW transmission line
        * second_length: '100um', -- The length of the main part of the second cpw
        * second_down_length: '100um', -- The length of the hanging part of the second cpw
        
        * coupling_space: '3um' -- The amount of ground plane between the two transmission lines
        * coupling_shift: '0um' -- Define the shift between the prime and second cpw edges
        * fillet: '25um'
        * mirror: False -- Flips the hanger around the y-axis
        * second_open_termination: True -- sets if the termination of the second line at the coupling side
          is an open to ground or short to ground
        * prime_open_termination: True -- sets if the termination of the prime line at the coupling side
          is an open to ground or short to ground
        * draw_prime: True -- sets if the primary cpw should be drawn
        * prime_down_connection: '0'/'1' sets the position of the second cpw hanging part (see the scheme)
    """
    component_metadata = Dict(short_name='cpw', _qgeometry_table_path='True')
    """Component metadata"""

    #Currently setting the primary CPW length based on the coupling_length
    #May want it to be it's own value that the user can control?
    default_options = Dict(prime_width='cpw_width',
                           prime_gap='cpw_gap',
                           prime_length='100um',
                           prime_down_length='0um',
                           second_width='cpw_width',
                           second_gap='cpw_gap',
                           second_length='100um',
                           second_down_length='100um',
                           coupling_space='3um',
                           coupling_shift='0um',
                           fillet='25um',
                           mirror=False,
                           second_open_termination=True,
                           prime_open_termination=False,
                           draw_prime =True,
                           prime_down_connection='0', # define side of down connection '0' or '1'
                          )
    """Default connector options"""

    TOOLTIP = """Generates a three pin (+) 
    structure comprised of a primary two 
    pin CPW transmission line, and a 
    secondary one pin neighboring CPW 
    transmission line that is 
    capacitively/inductively coupled 
    to the primary."""

    def make(self):
        """Build the component."""
        p = self.p

        second_flip = 1
        if p.mirror:
            second_flip = -1

        #Primary CPW
        if(p.prime_down_length==0):
            prime_cpw = draw.LineString([[-p.prime_length / 2, 0],
                                         [p.prime_length / 2, 0]])
        elif(p.prime_down_connection==0):
            prime_cpw = draw.LineString([[-p.prime_length / 2, p.prime_down_length],
                                         [-p.prime_length / 2, 0],
                                         [p.prime_length / 2, 0]])
        elif(p.prime_down_connection==1):
            prime_cpw = draw.LineString([[-p.prime_length / 2, 0],
                             [p.prime_length / 2, 0],
                             [p.prime_length / 2, p.prime_down_length]])

        prime_termination = 0
        if p.prime_open_termination:
            prime_termination = p.prime_gap
            
        if(p.prime_down_length==0):
            prime_cpw_etch = draw.LineString([[-p.prime_length / 2 - prime_termination, 0],
                                              [p.prime_length / 2, 0]])
        elif(p.prime_down_connection==0):
            prime_cpw_etch = draw.LineString([[-p.prime_length / 2, p.prime_down_length],
                                              [-p.prime_length / 2, 0],
                                              [p.prime_length / 2 + prime_termination, 0]])
        elif(p.prime_down_connection==1):
            prime_cpw_etch = draw.LineString([[-p.prime_length / 2 - prime_termination, 0],
                                              [p.prime_length / 2, 0],
                                              [p.prime_length / 2, p.prime_down_length]])

        # smart angle buffer to fix GDS
        prime_cpw_etch_tmp=prime_cpw_etch.buffer(p.fillet + p.prime_width/2 + p.prime_gap)
        
        if(p.prime_down_connection):
            prime_cpw_etch_tmp = draw.translate(prime_cpw_etch_tmp, -p.fillet, p.fillet)
        else:
            prime_cpw_etch_tmp = draw.translate(prime_cpw_etch_tmp, p.fillet, p.fillet)
            
        prime_cpw_etch = prime_cpw_etch.buffer(
            distance=(p.prime_width + 2 * p.prime_gap)/2,
            cap_style=CAP_STYLE.flat,
            join_style='mitre',
        )
        if(p.prime_down_length!=0):
            prime_cpw_etch=prime_cpw_etch.buffer(p.fillet - p.prime_width/2 - p.prime_gap).buffer(-p.fillet + p.prime_width/2 + p.prime_gap)
            prime_cpw_etch = prime_cpw_etch.intersection(prime_cpw_etch_tmp)

            
        #Secondary CPW
        second_down_length = p.second_down_length
        second_y = -p.prime_width / 2 - p.prime_gap - p.coupling_space - p.second_gap - p.second_width / 2
        second_cpw = draw.LineString(
            [[second_flip * (-p.prime_length / 2 + p.coupling_shift), second_y],
             [second_flip * (p.second_length - p.prime_length / 2 + p.coupling_shift), second_y],
             [
                 second_flip * (p.second_length - p.prime_length / 2 + p.coupling_shift),
                 second_y - second_down_length
             ]])

        second_termination = 0
        if p.second_open_termination:
            second_termination = p.second_gap

        second_cpw_etch = draw.LineString(
            [[
                second_flip * (-p.prime_length / 2 + p.coupling_shift - second_termination),
                second_y
            ], [second_flip * (p.second_length - p.prime_length / 2 + p.coupling_shift), second_y],
             [
                 second_flip * (p.second_length - p.prime_length / 2 + p.coupling_shift),
                 second_y - second_down_length
             ]])
    
        # smart angle buffer to fix GDS
        second_cpw_etch_tmp=second_cpw_etch.buffer(p.fillet + p.second_width/2 + p.second_gap)
        second_cpw_etch_tmp = draw.translate(second_cpw_etch_tmp, -p.fillet, -p.fillet)      
        second_cpw_etch = second_cpw_etch.buffer(
            distance=(p.second_width + 2 * p.second_gap)/2,
            cap_style=CAP_STYLE.flat,
            join_style='mitre',
        )
        if(p.second_down_length!=0):
            second_cpw_etch=second_cpw_etch.buffer(p.fillet - p.second_width/2 - p.second_gap).buffer(-p.fillet + p.second_width/2 + p.second_gap)
            second_cpw_etch = second_cpw_etch.intersection(second_cpw_etch_tmp)

        
        #Rotate and Translate
        c_items = [prime_cpw, second_cpw, second_cpw_etch, prime_cpw_etch]
        c_items = draw.rotate(c_items, p.orientation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [prime_cpw, second_cpw, second_cpw_etch, prime_cpw_etch] = c_items
        
        #Add to qgeometry tables
        if p.draw_prime:
            self.add_qgeometry('path', {'prime_cpw': prime_cpw},
                            width=p.prime_width, fillet=p.fillet)
            self.add_qgeometry('poly', {'prime_cpw_sub': prime_cpw_etch}, subtract=True)
            
        self.add_qgeometry('path', {'second_cpw': second_cpw},
                           width=p.second_width,
                           fillet=p.fillet)
        self.add_qgeometry('poly', {'second_cpw_sub': second_cpw_etch}, subtract=True)

        #Add pins
        prime_pin_list = prime_cpw.coords
        second_pin_list = second_cpw.coords

        if p.draw_prime:
            if(p.prime_down_length==0):
                self.add_pin('prime_out',
                            points=np.array(prime_pin_list),
                            width=p.prime_width,
                            input_as_norm=True)
                if(not p.prime_open_termination):
                    self.add_pin('prime_in',
                                points=np.array(prime_pin_list[::-1]),
                                width=p.prime_width,
                                input_as_norm=True)
                    
            elif(p.prime_down_connection==0):
                self.add_pin('prime_out',
                            points=np.array(prime_pin_list[1::-1]),
                            width=p.prime_width,
                            input_as_norm=True)               
                if(not p.prime_open_termination):
                    self.add_pin('prime_in',
                                points=np.array(prime_pin_list[1:]),
                                width=p.prime_width,
                                input_as_norm=True)
                    
            elif(p.prime_down_connection==1):
                self.add_pin('prime_out',
                            points=np.array(prime_pin_list[1:]),
                            width=p.prime_width,
                            input_as_norm=True)               
                if(not p.prime_open_termination):
                    self.add_pin('prime_in',
                                points=np.array(prime_pin_list[1::-1]),
                                width=p.prime_width,
                                input_as_norm=True)
                
        self.add_pin('second_out',
                     points=np.array(second_pin_list[1:]),
                     width=p.second_width,
                     input_as_norm=True)
        if(not p.second_open_termination):
            self.add_pin('second_in',
                         points=np.array(second_pin_list[1::-1]),
                         width=p.second_width,
                         input_as_norm=True)