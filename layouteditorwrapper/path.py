"""
This module contains classes and functions that are useful for drawing co-planar waveguide components.

The phrase 'package format' refers to the two-element (x, y) numpy array point format used everywhere in the package.
"""
from __future__ import division

import numpy as np

from . import wrapper


def from_increments(increments, origin=(0, 0)):
    """
    Return a list of points starting from the given origin and separated by the given increments.

    This function exists because it is often easier to specify paths in terms of the differences between points than in
    terms of the absolute values. Example:
    >>> from_increments(increments=[(200, 0), (0, 300)], origin=(100, 0))
    [np.array([100, 0]), np.array([300, 0]), np.array([300, 300])]

    :param increments: a list of point-like objects that will be the differences between consecutive returned points.
    :param origin: the starting point of the list.
    :return: a list of points in the package format.
    """
    points = [wrapper.to_point(origin)]
    for increment in [wrapper.to_point(point) for point in increments]:
        points.append(points[-1] + increment)
    return points


def smooth_path(points, radius, points_per_radian):
    """
    Return a list of smoothed points constructed by adding points to change the given corners into arcs.

    At each corner, points are added so that straight sections are connected by circular arcs that are tangent to the
    straight sections. If the given radius is too large there is no way to make this work, and the results will be ugly.
    The given radius should be smaller than about half the length of the shorted straight section. If several points lie
    on the same line, the redundant ones are removed. Note that the returned path will not contain any of the given
    points except for the starting and ending points.

    :param points: a list of points in package format.
    :param radius: the radius of the circular arcs used to connect the straight segments.
    :param points_per_radian: the number of points per radian of arc radius; usually 60 (about 1 per degree) is fine.
    :return: a list of smoothed points.
    """
    bends = []
    angles = []
    corners = []
    offsets = []
    for before, current, after in zip(points[:-2], points[1:-1], points[2:]):
        before_to_current = current - before
        current_to_after = after - current
        # The angle at which the path bends at the current point, in (-pi, pi)
        bend_angle = np.angle(np.inner(before_to_current, current_to_after) +
                              1j * np.cross(before_to_current, current_to_after))
        if np.abs(bend_angle) > 0:  # If the three points are co-linear then drop the current point
            # The distance from the corner point to the arc center
            h = radius / np.cos(bend_angle / 2)
            # The absolute angle of the arc center point, in (-pi, pi)
            theta = (np.arctan2(before_to_current[1], before_to_current[0]) +
                     bend_angle / 2 + np.sign(bend_angle) * np.pi / 2)
            # The offset of the arc center relative to the corner
            offset = h * np.array([np.cos(theta), np.sin(theta)])
            # The absolute angles of the new points (at least two), using the absolute center as origin
            arc_angles = (theta + np.pi + np.linspace(-bend_angle / 2, bend_angle / 2,
                                                      np.ceil(np.abs(bend_angle) * points_per_radian) + 1))
            bend = [current + offset + radius * np.array([np.cos(phi), np.sin(phi)]) for phi in arc_angles]
            bends.append(bend)
            angles.append(bend_angle)
            corners.append(current)
            offsets.append(offset)
    return bends, angles, corners, offsets


# ToDo: split this into separate classes
class Mesh(object):
    """
    This is a mix-in class that allows Element subclasses that have the same outlines to share mesh code.
    """

    def path_mesh(self):
        mesh_centers = []
        center_to_first_row = self.width / 2 + self.gap + self.mesh_border
        # Mesh the straight sections
        starts = [self.start] + [bend[-1] for bend in self.bends]
        ends = [bend[0] for bend in self.bends] + [self.end]
        for start, end in zip(starts, ends):
            v = end - start
            length = np.linalg.norm(v)
            phi = np.arctan2(v[1], v[0])
            R = np.array([[np.cos(phi), -np.sin(phi)],
                          [np.sin(phi), np.cos(phi)]])
            num_mesh_columns = np.floor(length / self.mesh_spacing)
            if num_mesh_columns == 0:
                continue
            elif num_mesh_columns == 1:
                x = np.array([length / 2])
            else:
                x = np.linspace(self.mesh_spacing / 2, length - self.mesh_spacing / 2, num_mesh_columns)
            y = center_to_first_row + self.mesh_spacing * np.arange(self.num_mesh_rows)
            xx, yy = np.meshgrid(np.concatenate((x, x)), np.concatenate((y, -y)))
            Rxy = np.dot(R, np.vstack((xx.flatten(), yy.flatten())))
            mesh_centers.extend(zip(start[0] + Rxy[0, :], start[1] + Rxy[1, :]))
        # Mesh the curved sections
        for row in range(self.num_mesh_rows):
            center_to_row = center_to_first_row + row * self.mesh_spacing
            for radius in [self.radius - center_to_row, self.radius + center_to_row]:
                if radius < self.mesh_spacing / 2:
                    continue
                for angle, corner, offset in zip(self.angles, self.corners, self.offsets):
                    num_points = np.round(radius * np.abs(angle) / self.mesh_spacing)
                    if num_points == 1:
                        max_angle = 0
                    else:
                        max_angle = (1 - 1 / num_points) * angle / 2
                    mesh_centers.extend([corner + offset +
                                         radius * np.array([np.cos(phi), np.sin(phi)]) for phi in
                                         (np.arctan2(-offset[1], -offset[0]) +
                                          np.linspace(-max_angle, max_angle, num_points))])
        return mesh_centers

    def trapezoid_mesh(self):
        mesh_centers = []
        v = self.end - self.start
        length = np.linalg.norm(v)
        phi = np.arctan2(v[1], v[0])
        R = np.array([[np.cos(phi), -np.sin(phi)],
                      [np.sin(phi), np.cos(phi)]])
        start_to_first_row = self.start_width / 2 + self.start_gap + self.start_mesh_border
        difference_to_first_row = self.end_width / 2 + self.end_gap + self.end_mesh_border - start_to_first_row
        num_mesh_columns = np.floor(length / self.mesh_spacing)
        if num_mesh_columns == 0:
            return []
        elif num_mesh_columns == 1:
            x = np.array([length / 2])
        else:
            x = np.linspace(self.mesh_spacing / 2, length - self.mesh_spacing / 2, num_mesh_columns)
        y = self.mesh_spacing * np.arange(self.num_mesh_rows, dtype=np.float)
        xxp, yyp = np.meshgrid(x, y)  # These correspond to the positive y-values
        y_shift = start_to_first_row + difference_to_first_row * x / length
        yyp += y_shift
        xx = np.concatenate((xxp, xxp))
        yy = np.concatenate((yyp, -yyp))  # The negative y-values are reflected
        Rxy = np.dot(R, np.vstack((xx.flatten(), yy.flatten())))
        mesh_centers.extend(zip(self.start[0] + Rxy[0, :], self.start[1] + Rxy[1, :]))
        return mesh_centers


class Path(list):
    """
    This class is a list subclass intended to hold Elements that are joined sequentially to form a path.
    """

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        """
        Draw all of the elements contained in this Path into the given cell. The Elements are drawn so that the origin
        of each element after the first is the end of the previous element.

        :param cell: The Cell into which the result is drawn.
        :param origin: The point to use for the origin of the first Element.
        :param positive_layer: An int representing the positive layer for boolean operations.
        :param negative_layer: An int representing the negative layer for boolean operations.
        :param result_layer: An int that is the layer on which the final result is drawn.
        :return: None.
        """
        # It's crucial to avoiding input modification that this also makes a copy.
        point = wrapper.to_point(origin)
        for element in self:
            element.draw(cell, point, positive_layer, negative_layer, result_layer)
            # NB: using += produces an error when casting int to float.
            point = point + element.end

    @property
    def start(self):
        return self[0].start

    @property
    def end(self):
        return np.sum(np.vstack(element.end for element in self), axis=0)

    @property
    def span(self):
        return self.end - self.start

    @property
    def length(self):
        return np.sum([element.length for element in self])


class Element(object):

    def __init__(self, points, round_to=None):
        points = wrapper.to_point_list(points)
        if round_to is not None:
            points = [round_to * np.round(p / round_to) for p in points]
        self._points = points

    @property
    def points(self):
        return self._points

    @property
    def start(self):
        return self._points[0]

    @property
    def end(self):
        return self._points[-1]

    @property
    def x(self):
        return np.array([point[0] for point in self.points])

    @property
    def y(self):
        return np.array([point[1] for point in self.points])

    @property
    def length(self):
        return np.sum(np.hypot(np.diff(self.x), np.diff(self.y)))

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        pass


class SmoothedElement(Element):

    def __init__(self, outline, radius, points_per_radian, round_to=None):
        super(SmoothedElement, self).__init__(points=outline, round_to=round_to)
        self.radius = radius
        self.points_per_radian = points_per_radian
        self.bends, self.angles, self.corners, self.offsets = smooth_path(self._points, radius, points_per_radian)

    @property
    def points(self):
        p = [self.start]
        for bend in self.bends:
            p.extend(bend)
        p.append(self.end)
        return p


class Trace(SmoothedElement):
    """
    A single positive trace that could be used for microstrip or for the center trace of a hybrid MKID.

    It can be drawn to overlap at either end with the adjacent elements.
    """

    def __init__(self, outline, width, start_overlap=0, end_overlap=0, radius=None, points_per_radian=60,
                 round_to=None):
        self.width = width
        self.start_overlap = start_overlap
        self.end_overlap = end_overlap
        if radius is None:
            radius = 2 * width
        super(Trace, self).__init__(outline=outline, radius=radius, points_per_radian=points_per_radian,
                                    round_to=round_to)

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        origin = wrapper.to_point(origin)
        points = [origin + point for point in self.points]
        cell.add_path(points=points, layer=result_layer, width=self.width)
        # Note that the overlap points are not stored or counted in the calculation of the length.
        if self.start_overlap > 0:
            v_start = points[0] - points[1]
            phi_start = np.arctan2(v_start[1], v_start[0])
            start_points = [points[0],
                            points[0] + self.start_overlap * np.array([np.cos(phi_start), np.sin(phi_start)])]
            cell.add_path(points=start_points, layer=result_layer, width=self.width)
        if self.end_overlap > 0:
            v_end = points[-1] - points[-2]
            phi_end = np.arctan2(v_end[1], v_end[0])
            end_points = [points[-1],
                          points[-1] + self.end_overlap * np.array([np.cos(phi_end), np.sin(phi_end)])]
            cell.add_path(points=end_points, layer=result_layer, width=self.width)


class CPW(SmoothedElement):

    def __init__(self, outline, width, gap, radius=None, points_per_radian=60, round_to=None):
        self.width = width
        self.gap = gap
        if radius is None:
            radius = width / 2 + gap
        super(CPW, self).__init__(outline=outline, radius=radius, points_per_radian=points_per_radian,
                                  round_to=round_to)

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        points = [wrapper.to_point(origin) + point for point in self.points]
        cell.add_path(points, negative_layer, self.width)
        cell.add_path(points, positive_layer, self.width + 2 * self.gap)
        cell.subtract(positive_layer=positive_layer, negative_layer=negative_layer, result_layer=result_layer)


class CPWBlank(SmoothedElement):

    def __init__(self, outline, width, gap, radius=None, points_per_radian=60, round_to=None):
        self.width = width
        self.gap = gap
        if radius is None:
            radius = width / 2 + gap
        super(CPWBlank, self).__init__(outline=outline, radius=radius, points_per_radian=points_per_radian,
                                       round_to=round_to)

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        points = [wrapper.to_point(origin) + point for point in self.points]
        cell.add_path(points, positive_layer, self.width + 2 * self.gap)
        cell.subtract(positive_layer=positive_layer, negative_layer=negative_layer, result_layer=result_layer)


class CPWMesh(CPW, Mesh):

    def __init__(self, outline, width, gap, mesh_spacing, mesh_border, mesh_radius, num_circle_points, num_mesh_rows,
                 radius=None, points_per_radian=60, round_to=None):
        super(CPWMesh, self).__init__(outline=outline, width=width, gap=gap, radius=radius,
                                      points_per_radian=points_per_radian, round_to=round_to)
        self.mesh_spacing = mesh_spacing
        self.mesh_radius = mesh_radius
        self.mesh_border = mesh_border
        self.num_circle_points = num_circle_points
        self.num_mesh_rows = num_mesh_rows
        self.mesh_centers = self.path_mesh()

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        super(CPWMesh, self).draw(cell=cell, origin=origin, positive_layer=positive_layer,
                                  negative_layer=negative_layer, result_layer=result_layer)
        for mesh_center in self.mesh_centers:
            cell.add_circle(origin=origin + mesh_center, radius=self.mesh_radius, layer=result_layer,
                            number_of_points=self.num_circle_points)


class CPWBlankMesh(CPWBlank, Mesh):

    def __init__(self, outline, width, gap, mesh_spacing, mesh_border, mesh_radius, num_circle_points, num_mesh_rows,
                 radius=None, points_per_radian=60, round_to=None):
        super(CPWBlankMesh, self).__init__(outline=outline, width=width, gap=gap, radius=radius,
                                           points_per_radian=points_per_radian, round_to=round_to)
        self.mesh_spacing = mesh_spacing
        self.mesh_radius = mesh_radius
        self.mesh_border = mesh_border
        self.num_circle_points = num_circle_points
        self.num_mesh_rows = num_mesh_rows
        self.mesh_centers = self.path_mesh()

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        super(CPWBlankMesh, self).draw(cell=cell, origin=origin, positive_layer=positive_layer,
                                       negative_layer=negative_layer, result_layer=result_layer)
        for mesh_center in self.mesh_centers:
            cell.add_circle(origin=origin + mesh_center, radius=self.mesh_radius, layer=result_layer,
                            number_of_points=self.num_circle_points)


class CPWElbowCoupler(SmoothedElement):

    def __init__(self, tip_point, elbow_point, joint_point, width, gap, radius=None, points_per_radian=60,
                 round_to=None):
        self.width = width
        self.gap = gap
        if radius is None:
            radius = width / 2 + gap
        super(CPWElbowCoupler, self).__init__(outline=[tip_point, elbow_point, joint_point], radius=radius,
                                              points_per_radian=points_per_radian, round_to=round_to)

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer, round_tip=True):
        points = [wrapper.to_point(origin) + point for point in self.points]
        cell.add_path(points, negative_layer, self.width)
        cell.add_path(points, positive_layer, self.width + 2 * self.gap)
        if round_tip:
            v = points[0] - points[1]
            theta = np.degrees(np.arctan2(v[1], v[0]))
            cell.add_polygon_arc(points[0], self.width / 2, self.width / 2 + self.gap, result_layer,
                                 theta - 90, theta + 90)
        else:
            raise NotImplementedError("Need to code this up.")
        cell.subtract(positive_layer=positive_layer, negative_layer=negative_layer, result_layer=result_layer)


class CPWElbowCouplerBlank(SmoothedElement):

    def __init__(self, tip_point, elbow_point, joint_point, width, gap, radius=None, points_per_radian=60,
                 round_to=None):
        self.width = width
        self.gap = gap
        if radius is None:
            radius = width / 2 + gap
        super(CPWElbowCouplerBlank, self).__init__(outline=[tip_point, elbow_point, joint_point], radius=radius,
                                                   points_per_radian=points_per_radian, round_to=round_to)

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer, round_tip=True):
        points = [wrapper.to_point(origin) + point for point in self.points]
        cell.add_path(points, result_layer, self.width + 2 * self.gap)
        if round_tip:
            v = points[0] - points[1]
            theta = np.degrees(np.arctan2(v[1], v[0]))
            cell.add_polygon_arc(points[0], 0, self.width / 2 + self.gap, result_layer, theta - 90, theta + 90)
        else:
            raise NotImplementedError("Need to code this up.")


class CPWElbowCouplerMesh(CPWElbowCoupler):
    pass


class CPWElbowCouplerBlankMesh(CPWElbowCouplerBlank):
    pass


class CPWTransition(Element):

    def __init__(self, start_point, end_point, start_width, end_width, start_gap, end_gap, round_to=None):
        super(CPWTransition, self).__init__(points=[start_point, end_point], round_to=round_to)
        self.start_width = start_width
        self.start_gap = start_gap
        self.end_width = end_width
        self.end_gap = end_gap

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        v = self.end - self.start
        phi = np.arctan2(v[1], v[0])
        rotation = np.array([[np.cos(phi), -np.sin(phi)],
                             [np.sin(phi), np.cos(phi)]])
        upper = [(0, self.start_width / 2),
                 (0, self.start_width / 2 + self.start_gap),
                 (self.length, self.end_width / 2 + self.end_gap),
                 (self.length, self.end_width / 2)]
        lower = [(x, -y) for x, y in upper]
        upper_rotated = [np.dot(rotation, wrapper.to_point(p).T).T for p in upper]
        lower_rotated = [np.dot(rotation, wrapper.to_point(p).T).T for p in lower]
        upper_rotated_shifted = [wrapper.to_point(origin) + self.start + p for p in upper_rotated]
        lower_rotated_shifted = [wrapper.to_point(origin) + self.start + p for p in lower_rotated]
        cell.add_polygon(upper_rotated_shifted, result_layer)
        cell.add_polygon(lower_rotated_shifted, result_layer)


class CPWTransitionBlank(Element):

    def __init__(self, start_point, end_point, start_width, end_width, start_gap, end_gap, round_to=None):
        super(CPWTransitionBlank, self).__init__(points=[start_point, end_point], round_to=round_to)
        self.start_width = start_width
        self.start_gap = start_gap
        self.end_width = end_width
        self.end_gap = end_gap

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        v = self.end - self.start
        phi = np.arctan2(v[1], v[0])
        rotation = np.array([[np.cos(phi), -np.sin(phi)],
                             [np.sin(phi), np.cos(phi)]])
        poly = [(0, self.start_width / 2 + self.start_gap),
                (self.length, self.end_width / 2 + self.end_gap),
                (self.length, -self.end_width / 2 - self.end_gap),
                (0, -self.start_width / 2 - self.start_gap)]
        poly_rotated = [np.dot(rotation, wrapper.to_point(p).T).T for p in poly]
        poly_rotated_shifted = [wrapper.to_point(origin) + self.start + p for p in poly_rotated]
        cell.add_polygon(poly_rotated_shifted, result_layer)


class CPWTransitionMesh(CPWTransition, Mesh):

    def __init__(self, start_point, end_point, start_width, end_width, start_gap, end_gap, mesh_spacing,
                 start_mesh_border, end_mesh_border, mesh_radius, num_circle_points, num_mesh_rows, round_to=None):
        super(CPWTransitionMesh, self).__init__(start_point=start_point, end_point=end_point, start_width=start_width,
                                                end_width=end_width, start_gap=start_gap, end_gap=end_gap,
                                                round_to=round_to)
        self.mesh_spacing = mesh_spacing
        self.start_mesh_border = start_mesh_border
        self.end_mesh_border = end_mesh_border
        self.mesh_radius = mesh_radius
        self.num_circle_points = num_circle_points
        self.num_mesh_rows = num_mesh_rows
        self.mesh_centers = self.trapezoid_mesh()

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        super(CPWTransitionMesh, self).draw(cell=cell, origin=origin, positive_layer=positive_layer,
                                            negative_layer=negative_layer, result_layer=result_layer)
        for mesh_center in self.mesh_centers:
            cell.add_circle(origin=origin + mesh_center, radius=self.mesh_radius, layer=result_layer,
                            number_of_points=self.num_circle_points)


class CPWTransitionBlankMesh(CPWTransitionBlank, Mesh):

    def __init__(self, start_point, end_point, start_width, end_width, start_gap, end_gap, mesh_spacing,
                 start_mesh_border, end_mesh_border, mesh_radius, num_circle_points, num_mesh_rows, round_to=None):
        super(CPWTransitionBlankMesh, self).__init__(start_point=start_point, end_point=end_point,
                                                     start_width=start_width, end_width=end_width,
                                                     start_gap=start_gap, end_gap=end_gap, round_to=round_to)
        self.mesh_spacing = mesh_spacing
        self.start_mesh_border = start_mesh_border
        self.end_mesh_border = end_mesh_border
        self.mesh_radius = mesh_radius
        self.num_circle_points = num_circle_points
        self.num_mesh_rows = num_mesh_rows
        self.mesh_centers = self.trapezoid_mesh()

    def draw(self, cell, origin, positive_layer, negative_layer, result_layer):
        super(CPWTransitionBlankMesh, self).draw(cell=cell, origin=origin, positive_layer=positive_layer,
                                                 negative_layer=negative_layer, result_layer=result_layer)
        for mesh_center in self.mesh_centers:
            cell.add_circle(origin=origin + mesh_center, radius=self.mesh_radius, layer=result_layer,
                            number_of_points=self.num_circle_points)
