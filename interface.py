"""
This module is an interface to pylayout.

The goal is to make design simpler. Where possible, this interface uses the same conventions and notation as the
LayoutEditor GUI, which are often different from those used by pylayout. I think the GUI conventions are usually
easier to use. For example, this interface by default uses the user unit, like the GUI, but can also use the integer
database units, like pylayout.

To avoid state mismatch issues, the classes created by this interface are nearly stateless. For example, every call
to drawing.cells generates a new list of Cell objects directly from the pylayout objects. The downside is that code
using this interface will generate multiple Cell objects that refer to the same pylayout cell. This should not cause
problems since the Cell and Element objects do not mirror the state of the corresponding pylayout objects.

Variables representing pylayout classes always have pl_ as a prefix.

In method docstrings the word *point* refers to a point with two coordinates. The classes use numpy arrays with shape
(2,) internally, but methods should accept anything that allows point[0] and point[1] to be indexed, such as a tuple.
"""
from __future__ import division
from collections import OrderedDict
import numpy as np
import pylayout


class Drawing(object):

    def __init__(self, pl_drawing, use_user_unit=True):
        """
        :param drawing: a pylayout.drawing instance.
        :param use_user_unit: a boolean that determines whether all values input to and returned from classes in this
        module are expected to be in user units or database units. All of the pylayout classes expect and return
        integer database units.
        :return: a Drawing instance.
        """
        self.pl_drawing = pl_drawing
        self.use_user_unit = use_user_unit

    @property
    def database_unit(self):
        """
        :return: the database unit in meters.
        """
        return self.pl_drawing.databaseunits

    @database_unit.setter
    def database_unit(self, unit):
        self.pl_drawing.databaseunits = unit

    @property
    def user_unit(self):
        """
        This is the ratio of the database unit to the user unit. All points are saved as integer values in database
        units, so this number is the data resolution in user units.
        """
        return self.pl_drawing.userunits

    @user_unit.setter
    def user_unit(self, unit):
        self.pl_drawing.userunits = unit

    def to_database_units(self, value_or_array):
        """
        Convert the given value or array to the database units. The behavior of this function depends on the value of
        the attribute use_user_unit in the following way: if this is True, then this function expects values in user
        units, which are scaled appropriately and rounded to the nearest integer; if False, this function expects
        values in database units, which are simply rounded to the nearest integer. The return value is always an int or
        a np.array of ints.

        :param value_or_array: a value or array to be converted to integer database units.
        :return: the converted int or int array.
        """
        try:
            if self.use_user_unit:
                return np.round(value_or_array / self.user_unit).astype(np.int)
            else:
                return np.round(value_or_array).astype(np.int)
        except AttributeError:  # not an array-like object
            if self.use_user_unit:
                return int(round(value_or_array / self.user_unit))
            else:
                return int(value_or_array)

    def from_database_units(self, value_or_array):
        try:
            if self.use_user_unit:
                return (value_or_array * self.user_unit).astype(np.float)
            else:
                return value_or_array.astype(np.int)
        except AttributeError:
            if self.use_user_unit:
                return float(value_or_array * self.user_unit)
            else:
                return int(value_or_array)

    @property
    def cells(self):
        """
        Cells are uniquely specified by their name. New cells are prepended to the internal linked list, so the index of
        a cell will change as new cells are added.

        :return: an OrderedDict of all cells in the drawing, with cell name keys and Cell object values.
        """
        cell_dict = OrderedDict()
        current = self.pl_drawing.firstCell
        while current is not None:
            cell = Cell(current.thisCell, self)
            cell_dict[cell.name] = cell
            current = current.nextCell
        return cell_dict

    def _to_np_point(self, indexable):
        return np.array([indexable[0], indexable[1]])  #, dtype={True: np.float, False: np.int}[self.use_user_unit])

    def _np_to_pyqt(self, array):
        """
        Create a point without adding the point to the drawing and scale the coordinates to the database units.

        :param array: a two-element numpy array containing the x- and y-coordinates of the point in either user units or
        database units; see __init__().
        :return: a PyQt4.QtCore.QPoint instance that contains the given coordinates in integer database units.
        """
        return pylayout.point(self.to_database_units(array[0]), self.to_database_units(array[1]))

    def _pyqt_to_np(self, point):
        return self.from_database_units(np.array([point.x(), point.y()]))

    def _to_point_array(self, list_of_np_arrays):
        pa = pylayout.pointArray(len(list_of_np_arrays))
        for i, array in enumerate(list_of_np_arrays):
            pa.setPoint(i, self._np_to_pyqt(array))
        return pa

    def _to_list_of_np_arrays(self, point_array):
        array_list = []
        for i in range(point_array.size()):
            array_list.append(self._pyqt_to_np(point_array.point(i)))
        return array_list

    def add_cell(self, name=None):
        if name in self.cells:
            raise ValueError("Cell name already exists.")
        if name is None or not name:
            for n in range(1, len(self.cells) + 2):
                name = "noname_{}".format(n)
                if name not in self.cells:
                    break
        pl_cell = self.pl_drawing.addCell().thisCell
        pl_cell.cellName = name
        return Cell(pl_cell, self)


class Cell(object):
    def __init__(self, cell, drawing):
        self.pl_cell = cell
        self.drawing = drawing

    @property
    def name(self):
        return self.pl_cell.cellName.toAscii().data()

    @name.setter
    def name(self, name):
        if name != self.name and name in self.drawing.cells:
            raise ValueError("Cell name already exists.")
        self.pl_cell.cellName = str(name)

    @property
    def elements(self):
        """
        Generate and return a list of all elements in the cell. Since pylayout elements do not have an internal name,
        unlike cells, there is no obvious way to create dictionary keys for them.

        Note that new elements are prepended to the internal linked list as they are added to a cell, so the index of
        each element is not constant.

        :return: a list of Element objects in this Cell.
        """
        element_list = []
        current = self.pl_cell.firstElement
        while current is not None:
            element_list.append(instantiate_element(current.thisElement, self.drawing))
            current = current.nextElement
        return element_list

    def __str__(self):
        return 'Cell {}: {}'.format(self.name, [str(e) for e in self.elements])

    def add_cell(self, cell, origin):
        """
        Add a single cell to this cell.

        :param cell: the Cell object to add to this cell.
        :param origin: a point containing the origin x- and y-coordinates.
        :return: a Cellref object with a reference to the given Cell.
        """
        pl_cell = self.pl_cell.addCellref(cell.pl_cell, self.drawing._np_to_pyqt(self.drawing._to_np_point(origin)))
        return Cellref(pl_cell, self.drawing)

    def add_cell_array(self, cell, origin, step_x=(0, 0), step_y=(0, 0), repeat_x=1, repeat_y=1):
        """
        Add an array of cells to this cell.

        :param cell: the Cell object to add to this cell.
        :param origin: a point containing the origin x- and y-coordinates.
        :param step_x: a point containing the x- and y-increment for all cells in each row.
        :param step_y: a point containing the x- and y-increment for all cells in each column.
        :param repeat_x: the number of columns.
        :params repeat_y: the number of rows.
        :return: a CellrefArray object with a reference to the given Cell.
        """
        repeat_x = int(repeat_x)
        repeat_y = int(repeat_y)
        # Horrible, but true: the constructor for this object expects three points that are different from both the
        # points returned by getPoints() and the GUI interface points.
        pl_origin = self.drawing._to_np_point(origin)
        pl_total_x = repeat_x * self.drawing._to_np_point(step_x) + pl_origin
        pl_total_y = repeat_y * self.drawing._to_np_point(step_y) + pl_origin
        point_array = self.drawing._to_point_array([pl_origin, pl_total_x, pl_total_y])
        pl_cell_array = self.pl_cell.addCellrefArray(cell.pl_cell, point_array, repeat_x, repeat_y)
        return CellrefArray(pl_cell_array, self.drawing)

    def add_box(self, x, y, width, height, layer):
        """
        Add a rectanglular box to this cell and return the corresponding object.

        :param x: the x-coordinate of the origin.
        :param y: the y-coordinate of the origin.
        :param width: the horizontal width of the box, positive if the box is to extend to the right from the origin.
        :param width: the vertical height of the box, positive if the box is to extend upward from the origin.
        :param layer: the layer on which the box is created.
        :return: a Box object.
        """
        pl_box = self.pl_cell.addBox(self.drawing.to_database_units(x),
                                     self.drawing.to_database_units(y),
                                     self.drawing.to_database_units(width),
                                     self.drawing.to_database_units(height),
                                     int(layer))
        return Box(pl_box, self.drawing)

    def add_circle(self, origin, radius, layer, number_of_points=0):
        """
        Add a circular polygon to this cell and return the corresponding object. Note that pylayout considers any
        regular polygon with 8 or more points to be a circle, and once created a circle has no special properties.

        :param origin: a point containing the (x, y) coordinates of the circle center.
        :param radius: the circle radius.
        :param layer: the layer on which the circle is created.
        :param number_of_points: the number of unique points to use in creating the circle; the default of 0 uses the
        current pylayout default.
        :return: a Circle object.
        """
        pl_circle = self.pl_cell.addCircle(int(layer), self.drawing._np_to_pyqt(self.drawing._to_np_point(origin)),
                                           self.drawing.to_database_units(radius), int(number_of_points))
        return Circle(pl_circle, self.drawing)

    def add_polygon(self, points, layer):
        """
        Add a polygon to this cell and return the corresponding object. If the given list of points does not close,
        pylayout will automatically add the first point to the end of the point list in order to close it.

        :param points: an iterable of points that are the vertices of the polygon.
        :param layer: the layer on which the polygon is created.
        :return: a Polygon object.
        """
        pl_polygon = self.pl_cell.addPolygon(self.drawing._to_point_array(points), int(layer))
        return Polygon(pl_polygon, self.drawing)

    def add_path(self, points, layer, width=None, cap=None):
        """
        Add a path to this cell and return the corresponding object. A path may be closed or open.

        :param points: an iterable of points that are the vertices of the path.
        :param layer: the layer on which the path is created.
        :param width: the width of the path.
        :param cap: the cap style of the path; the default of None will create a path with the current default cap.
        :return: a Path object.
        """
        pl_path = self.pl_cell.addPath(self.drawing._to_point_array(points), int(layer))
        path = Path(pl_path, self.drawing)
        if width is not None:
            path.width = float(width)
        if cap is not None:
            path.cap = int(cap)
        return path

    def add_text(self, origin, text, layer, height=None):
        """
        Add text to this cell and return the corresponding object.

        :param origin: a point representing the origin of the text object, which appears to be to the upper left of
        where the text begins.
        :param text: a string representing the text to be displayed.
        :param layer: the layer on which the text is created.
        :param height: the height of the text; positive values are interpreted as user units, negative values create
        a fixed height in pixels, and the default uses the current default.
        :return: a Text object.
        """
        pl_text = self.pl_cell.addText(int(layer), self.drawing._np_to_pyqt(self.drawing._to_np_point(origin)),
                                       str(text))
        text_ = Text(pl_text, self.drawing)
        if height is not None:
            text_.height = height
        return text_


def instantiate_element(pl_element, drawing):
    elements = (Box, Cellref, CellrefArray, Circle, Path, Polygon, Text)
    for element in elements:
        if getattr(pl_element, 'is' + element.__name__)():
            return element(pl_element, drawing)
    raise ValueError("Unknown pylayout element.")


# TODO: think about using a reference to the parent cell instead of to the drawing.
class Element(object):

    def __init__(self, pl_element, drawing):
        self.pl_element = pl_element
        self.drawing = drawing

    @property
    def points(self):
        return self.drawing._to_list_of_np_arrays(self.pl_element.getPoints())

    @points.setter
    def points(self, points):
        self.pl_element.setPoints(self.drawing._to_point_array(points))

    @property
    def data_type(self):
        return self.pl_element.getDatatype()

    @data_type.setter
    def data_type(self, data_type):
        self.pl_element.setDatatype(int(data_type))

    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, self.points)

    @property
    def angle(self):
        return self.pl_element.getTrans().getAngle()

    @angle.setter
    def angle(self, angle):
        transformation = self.pl_element.getTrans()
        # Bizarrely, strans.rotate(angle) rotates by -angle; these lines rotate to zero then to the desired angle.
        transformation.rotate(transformation.getAngle())
        transformation.rotate(-angle)
        self.pl_element.setTrans(transformation)

    @property
    def scale(self):
        """
        The scale of the transformation. The returned value is always positive. However, setting a negative scale will
        produce a rotation by 180 degrees along with a scaling by the absolute value of the given scale.
        """
        return self.pl_element.getTrans().getScale()

    @scale.setter
    def scale(self, scale):
        transformation = self.pl_element.getTrans()
        transformation.scale(scale / transformation.getScale())
        self.pl_element.setTrans(transformation)

    @property
    def mirror_x(self):
        return self.pl_element.getTrans().getMirror_x()

    @mirror_x.setter
    def mirror_x(self, mirror):
        transformation = self.pl_element.getTrans()
        if bool(mirror) ^ transformation.getMirror_x():
            transformation.toggleMirror_x()
        self.pl_element.setTrans(transformation)

    def reset_transformation(self):
        transformation = self.pl_element.getTrans()
        transformation.reset()
        self.pl_element.setTrans(transformation)


# TODO: remove comments to enable the layer property after the next update.
class LayerElement(Element):
    """
    This class is identical to Element except that it adds a layer property for Elements that exist on a single
    layer, which is all of them except for the Cellref and CellrefArray classes.
    """
    pass

    """
    @property
    def layer(self):
        return self.pl_element.layerNum

    # Verify that this is settable
    @layer.setter
    def layer(self, layer):
        self.pl_element.layerNum = int(layer)
    """


class CellElement(Element):

    def __init__(self, pl_element, drawing):
        super(CellElement, self).__init__(pl_element, drawing)
        self.cell = Cell(pl_element.depend(), drawing)


class Cellref(CellElement):

    def __str__(self):
        return 'Cell {} at ({:.3f}, {:.3f})'.format(self.cell.name, self.origin[0], self.origin[1])

    @property
    def origin(self):
        return self.points[0]

    @origin.setter
    def origin(self, origin):
        self.points = [self.drawing._to_np_point(origin)]


class CellrefArray(CellElement):

    def __str__(self):
        return 'Cell {}: {} {} by {}'.format(self.cell.name, self.points, self.repeat_x, self.repeat_y)

    @classmethod
    def _to_pylayout(cls, points):
        origin, step_x, step_y = points
        return [origin, step_x + origin, step_y + origin]

    @classmethod
    def _from_pylayout(cls, points):
        origin, pl_x, pl_y = points
        return [origin, pl_x - origin, pl_y - origin]

    @property
    def points(self):
        return self._from_pylayout(self.drawing._to_list_of_np_arrays(self.pl_element.getPoints()))

    @points.setter
    def points(self, points):
        self.pl_element.setPoints(self.drawing._to_point_array(self._to_pylayout(points)))

    @property
    def origin(self):
        return self.points[0]

    @origin.setter
    def origin(self, origin):
        self.points = [self.drawing._to_np_point(origin), self.points[1], self.points[2]]

    @property
    def step_x(self):
        return self.points[1]

    @step_x.setter
    def step_x(self, step_x):
        self.points = [self.points[0], self.drawing._to_np_point(step_x), self.points[2]]

    @property
    def step_y(self):
        return self.points[2]

    @step_y.setter
    def step_y(self, step_y):
        self.points = [self.points[0], self.points[1], self.drawing._to_np_point(step_y)]

    @property
    def repeat_x(self):
        return self.pl_element.getNx()

    @repeat_x.setter
    def repeat_x(self, repeat):
        self.pl_element.setNx(int(repeat))

    @property
    def repeat_y(self):
        return self.pl_element.getNy()

    @repeat_y.setter
    def repeat_y(self, repeat):
        self.pl_element.setNy(int(repeat))


class Box(LayerElement):

    @property
    def _points(self):
        (x_upper_left, y_upper_left), (x_lower_right, y_lower_right) = self.points
        x = x_upper_left
        y = y_lower_right
        width = x_lower_right - x_upper_left
        height = y_upper_left - y_lower_right
        return x, y, width, height

    @property
    def x(self):
        return self._points[0]

    @property
    def y(self):
        return self._points[1]

    @property
    def width(self):
        return self._points[2]

    @property
    def height(self):
        return self._points[3]


class Circle(LayerElement):
    """
    LayoutEditor considers any regular polygon with more than 8 points to be a circle.
    """
    @property
    def center(self):
        # The last point is always the same as the first.
        x = np.mean([p[0] for p in self.points[:-1]])
        y = np.mean([p[1] for p in self.points[:-1]])
        return self.drawing.from_database_units(self.drawing.to_database_units(np.array([x, y])))

    @property
    def radius(self):
        return np.sqrt(np.sum((self.points[0] - self.center)**2))


class Path(LayerElement):

    @property
    def width(self):
        return self.pl_element.getWidth()

    @width.setter
    def width(self, width):
        self.pl_element.setWidth(self.drawing.to_database_units(width))

    @property
    def cap(self):
        return self.pl_element.getCap()

    @cap.setter
    def cap(self, cap):
        self.pl_element.setCap(int(cap))


class Polygon(LayerElement):
    pass


class Text(LayerElement):

    def __str__(self):
        return 'Text "{}" at ({:.3f}, {:.3f})'.format(self.text, self.origin[0], self.origin[1])

    @property
    def text(self):
        return self.pl_element.getName().toAscii().data()

    @text.setter
    def text(self, text):
        self.pl_element.setName(text)

    @property
    def height(self):
        return self.drawing.from_database_units(self.pl_element.getWidth())

    @height.setter
    def height(self, height):
        self.pl_element.setWidth(self.drawing.to_database_units(height))

    @property
    def origin(self):
        return self.points[0]

    @origin.setter
    def origin(self, origin):
        self.points = [self.drawing._to_np_point(origin)]
