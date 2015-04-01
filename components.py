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
    :return: an interface.Cell object containing the IDC.
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


def meander(drawing, length, spacing, width, turns, layer, cell_name=None):
    """
    Create and return a new interface.Cell object containing a meandered inductor with the given parameters. The
    lower left corner of the meander is at (0, 0), and the center of the first trace is at (width / 2, width / 2).
    The upper left corner is at (0, length). The lower right corner is at
    (2 * turns * width + (2 * turns - 1) * spacing, 0)
    because the final turn has no connecting piece to the right.

    :param drawing: drawing: the interface.Drawing object to which the new cell should be added.
    :param length: the length of each turn, from outer edge to outer edge.
    :param spacing: the edge-to-edge spacing between traces.
    :param width: the width of the trace.
    :param turns: the number of out-and-back turns.
    :param layer: the layer on which to create the meander.
    :param cell_name: the name of the cell; the default includes all the parameters.
    :return: an interface.Cell object containing the meander.
    """
    if cell_name is None:
        cell_name = 'meander_{:.3f}_{:.3f}_{:.3f}_{:.0f}_{:.0f}'.format(length, spacing, width, turns, layer)

    cell = drawing.add_cell(cell_name)
    points = [np.array([width / 2, width / 2])]
    for turn in range(turns):
        points.append(points[-1] + np.array([0, length - width]))
        points.append(points[-1] + np.array([spacing + width, 0]))
        points.append(points[-1] + np.array([0, -(length - width)]))
        points.append(points[-1] + np.array([spacing + width, 0]))
    points.pop()
    cell.add_path(points, int(layer), width=width, cap=2)
    return cell


def double_meander(drawing, length, spacing, width, turns, layer, cell_name=None):
    """
    Create and return a new interface.Cell object containing a double-wound meandered inductor with the given
    parameters. The lower left corner of the meander is at (0, 0), and the center of the first trace is at (width /
    2, width / 2). The upper left corner is at (0, length). The lower right corner is at
    (2 * turns * width + (2 *
    turns - 1) * spacing, 0)
    because the final turn has no connecting piece to the right.

    :param drawing: drawing: the interface.Drawing object to which the new cell should be added.
    :param length: the length of each turn, from outer edge to outer edge.
    :param spacing: the edge-to-edge spacing between traces.
    :param width: the width of the trace.
    :param turns: the number of turns, where each turn is a pair of traces.
    :param layer: the layer on which to create the meander.
    :param cell_name: the name of the cell; the default includes all the parameters.
    :return: an interface.Cell object containing the meander.
    """
    if cell_name is None:
        cell_name = 'double_meander_{:.3f}_{:.3f}_{:.3f}_{:.0f}_{:.0f}'.format(length, spacing, width, turns, layer)

    cell = drawing.add_cell(cell_name)
    start = [np.array([width / 2, width / 2 + width + spacing])]
    end = [np.array([width / 2 + width + spacing, width / 2])]
    horizontal = width + spacing
    vertical = (length - width) - horizontal
    for turn in range(turns):
        if turn % 2:
            start.append(start[-1] + np.array([0, -vertical]))
            end.append(end[-1] + np.array([0, -vertical]))
            start.append(start[-1] + np.array([horizontal, 0]))
            end.append(end[-1] + np.array([3 * horizontal, 0]))
        else:
            start.append(start[-1] + np.array([0, vertical]))
            end.append(end[-1] + np.array([0, vertical]))
            start.append(start[-1] + np.array([3 * horizontal, 0]))
            end.append(end[-1] + np.array([horizontal, 0]))
    # Fix the first point.
    start[0] = np.array([width / 2, width / 2])
    # Delete the last horizontal connection and close the loop.
    start.pop()
    end.pop()
    if turns % 2:
        end[-1] = np.array([end[-1][0], start[-1][1]])
    else:
        start[-1] = np.array([start[-1][0], end[-1][1]])
    for point in reversed(end):
        start.append(point)
    cell.add_path(start, int(layer), width=width, cap=2)
    return cell


