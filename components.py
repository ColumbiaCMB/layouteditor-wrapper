from __future__ import division
import numpy as np
# This should be from layouteditor import interface, but that doesn't resolve currently.
import interface

def interdigitated_capacitor(drawing, space, length, width, base, offset, turns, layer, cell_name=None):
    """
    Create and return a new interface.Cell object containing an interdigitated capacitor with the given parameters.
    This function is a copy of combdrive.layout from the LayoutEditor shapes library.

    :param drawing: the interface.Drawing object to which the new cell should be added.
    :param space: the spacing between tines.
    :param length: the length of each tine from base to end.
    :param width: the width of each tine.
    :param base: the size of the base connecting the tines on each end.
    :param offset: the distance from the base to the tines of the opposite group.
    :param turns: the number of pairs of tines; there is an extra tine on the bottom.
    :param layer: the layer on which to create the IDC.
    :param cell_name: the name of the cell; the default includes all the parameters.
    :return:
    """
    if cell_name is None:
        cell_name = 'IDC_{:.3f}_{:.3f}_{:.3f}_{:.3f}_{:.3f}_{:.0f}_{:.0f}'.format(space, length, width, base, offset,
                                                                                  turns, layer)
    cell = drawing.add_cell(cell_name)
    for turn in range(turns):
        left_lower = (width + space) * 2 * turn
        left_upper = (width + space) * (2 * turn + 1)
        cell.add_box(left_lower, base, width, length, layer)
        cell.add_box(left_upper, base + offset, width, length, layer)
    total_width = 2 * turns * (width + space) + width
    cell.add_box(total_width - width, base, width, length, layer)  # rightmost tine
    cell.add_box(0, 0, total_width, base, layer)  # lower base
    cell.add_box(0, base + length + offset, total_width, base, layer)  # upper base
    return cell

