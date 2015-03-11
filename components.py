from __future__ import division
import numpy as np
# This should be from layouteditor import interface, but that doesn't resolve currently.
import interface

def interdigital_capacitor(drawing, space, length, width, base, offset, turns, layer, cell_name=None):
    if cell_name is None:
        cell_name = 'IDC_{:.3f}_{:.3f}_{:.3f}_{:.3f}_{:.3f}_{:.0f}_{:.0f}'.format(space, length, width, base, offset,
                                                                                  turns, layer)
    if drawing.pl_drawing.existCellname(cell_name):
        raise ValueError("Cell already exists: {}".format(cell_name))
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

