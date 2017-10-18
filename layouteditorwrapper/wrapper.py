"""
This module is a wrapper for pylayout, the Python module of LayoutEditor.

This module includes several types of objects that each wrap a pylayout object. The naming conventions for pylayout
objects are the following: in methods and functions, pylayout objects have a pyl_ prefix; as attributes of wrapper
classes, the attribute .pyl is the wrapped object. For example, the constructor for Cell includes pyl_cell,
which is a pylayout.cell object; also, if cell is a wrapper.Cell object, then cell.pyl is the underlying pylayout.cell
object.

Where possible, the classes use the same conventions and notation as the LayoutEditor GUI, which are often different
from those used by pylayout. I think the GUI conventions are usually easier to use. For example, this interface by
default uses the user unit, like the GUI, but can also use the integer database units, like pylayout.

The classes representing the objects in a drawing are nearly stateless wrappers for the underlying pylayout objects.
For example, every call to drawing.cells generates a new list of Cell objects. Since the wrappers store no state,
there is no need for them to be unique. These can be cached for speed, if necessary.

In method docstrings the word *point* refers to a point with two coordinates. The classes use numpy arrays with shape
(2,) internally, but methods should accept anything that allows point[0] and point[1] to be indexed, such as a tuple.
"""
from __future__ import division
import sys
from collections import OrderedDict

import numpy as np
# These shenanigans ensure that the bundled PyQt4 and sip are imported instead of any newer versions.
# For this to work, the distributed pylayout directory should be available on the PYTHONPATH as pylayout and must be
# made into a valid package by adding an __init__.py file.
import pylayout
sys.path.insert(0, pylayout.__path__[0])
from PyQt4 import QtCore, QtGui
from pylayout import pylayout
sys.path.pop(0)

# The two following simple functions are available to code that uses (lists of) numpy arrays as points.
# This makes it easy for methods to accept lists of tuples, for example.


def to_point(indexable):
    """
    Return a numpy array in the two-dimensional point format used by this module.

    :param indexable: an indexable object with integer indices 0 and 1
    :return: a numpy array with shape (2,) containing the values at these two indices.
    """
    return np.array([indexable[0], indexable[1]])


def to_point_list(iterable):
    """
    Return a list of numpy arrays in the two-dimensional point format used by this module.

    :param iterable: an iterable of indexable objects that all have integer indices 0 and 1.
    :return: a list of numpy arrays with shape (2,) containing the values at these two indices.
    """
    return [to_point(point) for point in iterable]


def instantiate_element(pyl_element, drawing):
    """
    Instantiate the appropriate wrapper class for the given pylayout element type.

    :param pyl_element: a pylayout element object.
    :param drawing: a Drawing object.
    :return: a wrapper instance for the pylayout element.
    """
    elements = (Box, Cellref, CellrefArray, Circle, Path, Polygon, Text)
    for element in elements:
        if getattr(pyl_element, 'is' + element.__name__)():
            return element(pyl_element, drawing)
    raise ValueError("Unknown pylayout element.")


class Layout(QtCore.QObject):
    """Wrap a pylayout.layout object."""

    def __init__(self, gui=True):
        """
        Create a new LayoutEditor instance.

        :param gui: if True, the splash screen and LayoutEditor window will appear, as usual; if False, neither window
            will appear, but editing using this module will still work.
        """
        super(Layout, self).__init__()
        if gui:  # The application doesn't work unless GUIenabled=True, but we can simply not show it
            self.app = QtGui.QApplication([], True)
            self.app.quitOnLastWindowClosed = True
            splashscreen = pylayout.splash(QtGui.QPixmap(":/splash"))
            splashscreen.show()
            self.pyl = pylayout.project.newLayout()
            splashscreen.finish(self.pyl)
            self.pyl.show()
        else:
            self.app = QtGui.QApplication([], True)
            self.pyl = pylayout.project.newLayout()

    def show_latest(self):
        self.pyl.drawing.currentCell = self.pyl.drawing.firstCell.thisCell
        self.pyl.guiUpdate()
        self.pyl.drawing.scaleFull()

    def drawing(self, use_user_unit=True, auto_number=False):
        return Drawing(self.pyl.drawing, use_user_unit=use_user_unit, auto_number=auto_number)


class Drawing(object):
    """Wrap a pylayout.drawingField object."""

    def __init__(self, pyl_drawing, use_user_unit=True, auto_number=False):
        """
        :param pyl_drawing: a pylayout.drawingField instance.
        :param use_user_unit: a boolean that determines whether all values input to and returned from classes in this
        module are expected to be in user units or database units. All of the pylayout classes expect and return
        integer database units.
        :param auto_number: a boolean -- if True, the add_cell() method  will append an integer to the names of all
            cells it creates in this drawing.
        :return: a Drawing instance.
        """
        self.pyl = pyl_drawing
        self.use_user_unit = use_user_unit
        self.auto_number = auto_number
        if auto_number:
            self._cell_number = 0

    @property
    def database_unit(self):
        """
        :return: the database unit in meters.
        """
        return self.pyl.databaseunits

    @database_unit.setter
    def database_unit(self, unit):
        self.pyl.databaseunits = unit

    @property
    def user_unit(self):
        """
        This is the ratio of the database unit to the user unit. All points are saved as integer values in database
        units, so this number is the data resolution in user units.
        """
        return self.pyl.userunits

    @user_unit.setter
    def user_unit(self, unit):
        self.pyl.userunits = unit

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
        except AttributeError:  # not an array-like object
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
        n_cells = 0
        cell_dict = OrderedDict()
        current = self.pyl.firstCell
        while current is not None:
            cell = Cell(current.thisCell, self)
            cell_dict[cell.name] = cell
            n_cells += 1
            current = current.nextCell
        if n_cells != len(cell_dict):
            raise RuntimeError("Duplicate cell name.")
        return cell_dict

    def _np_to_pyqt(self, array):
        """
        Create a point (without adding it to the drawing) and scale the coordinates to the database units.

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

    def add_cell(self, name):
        """
        Return a new Cell object that wraps a pylayout.cell object.

        If self.auto_number is True, the string '_x' will be appended to the given cell name, where x is the number of
        cells that have been created so far by this class. This allows code to repeatedly call this method with the same
        name string without producing an error, since the appended number guarantees that their names will be unique.

        :param name: a string that is the name of the new cell.
        :return: a Cell object.
        """
        if self.auto_number:
            name = '{}_{}'.format(name, self._cell_number)
            self._cell_number += 1
        pyl_cell = self.pyl.addCell().thisCell
        pyl_cell.cellName = name
        # Adding a cell does not update currentCell. Without the line below, boolean operations (and probably others)
        #  will operate on currentCell instead of the cell created by this method.
        # ToDo: this may no longer be necessary
        self.pyl.currentCell = pyl_cell
        return Cell(pyl_cell, self)


class Cell(object):
    """Wrap a pylayout.cell object."""

    def __init__(self, pyl_cell, drawing):
        self.pyl = pyl_cell
        self.drawing = drawing

    @property
    def name(self):
        return self.pyl.cellName.toAscii().data()

    @name.setter
    def name(self, name):
        if name != self.name and name in self.drawing.cells:
            raise ValueError("Cell name already exists.")
        self.pyl.cellName = str(name)

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
        current = self.pyl.firstElement
        while current is not None:
            element_list.append(instantiate_element(current.thisElement, self.drawing))
            current = current.nextElement
        return element_list

    def __str__(self):
        return 'Cell {}: {}'.format(self.name, [str(e) for e in self.elements])

    def subtract(self, positive_layer, negative_layer, result_layer, delete=True):
        """
        Perform the boolean operation
        positive - negative = result
        on the given layers.

        :param positive_layer: Structures on this layer remain unless subtracted.
        :param negative_layer: Structures on this layer are subtracted from the positive layer.
        :param result_layer: The structures resulting from the subtraction are created on this layer.
        :param delete: if True, delete all structures on the positive and negative layers after the subtraction.
        :return: None
        """
        self.drawing.pyl.setCell(self.pyl)
        bh = pylayout.booleanHandler(self.drawing.pyl)
        bh.boolOnLayer(positive_layer, negative_layer, result_layer, pylayout.string('A-B'), 0, 0, 0)
        if delete:
            self.drawing.pyl.deleteLayer(positive_layer)
            self.drawing.pyl.deleteLayer(negative_layer)

    def add_cell(self, cell, origin, angle=0):
        """
        Add a single cell to this cell.

        :param cell: the Cell object to add to this cell.
        :param origin: a point containing the origin x- and y-coordinates.
        :param angle: a float representing the cell orientation in degrees.
        :return: a Cellref object with a reference to the given Cell.
        """
        pyl_cell = self.pyl.addCellref(cell.pyl, self.drawing._np_to_pyqt(to_point(origin)))
        cell = Cellref(pyl_cell, self.drawing)
        cell.angle = angle
        return cell

    def add_cell_array(self, cell, origin=(0, 0), step_x=(0, 0), step_y=(0, 0), repeat_x=1, repeat_y=1, angle=0):
        """
        Add an array of cells to this cell.

        :param cell: the Cell object to add to this cell.
        :param origin: a point containing the origin x- and y-coordinates.
        :param step_x: a point containing the x- and y-increment for all cells in each row.
        :param step_y: a point containing the x- and y-increment for all cells in each column.
        :param repeat_x: the number of columns.
        :params repeat_y: the number of rows.
        :param angle: a float representing the cell orientation in degrees.
        :return: a CellrefArray object with a reference to the given Cell.
        """
        repeat_x = int(repeat_x)
        repeat_y = int(repeat_y)
        # Strange but true: the constructor for this object expects three points that are different from both the
        # points returned by getPoints() and the GUI interface points.
        pyl_origin = to_point(origin)
        pyl_total_x = repeat_x * to_point(step_x) + pyl_origin
        pyl_total_y = repeat_y * to_point(step_y) + pyl_origin
        point_array = self.drawing._to_point_array([pyl_origin, pyl_total_x, pyl_total_y])
        pyl_cell_array = self.pyl.addCellrefArray(cell.pyl, point_array, repeat_x, repeat_y)
        cell_array = CellrefArray(pyl_cell_array, self.drawing)
        cell_array.angle = angle
        return cell_array

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
        pyl_box = self.pyl.addBox(self.drawing.to_database_units(x),
                                  self.drawing.to_database_units(y),
                                  self.drawing.to_database_units(width),
                                  self.drawing.to_database_units(height),
                                  int(layer))
        return Box(pyl_box, self.drawing)

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
        pyl_circle = self.pyl.addCircle(int(layer), self.drawing._np_to_pyqt(to_point(origin)),
                                       self.drawing.to_database_units(radius), int(number_of_points))
        return Circle(pyl_circle, self.drawing)

    def add_polygon(self, points, layer):
        """
        Add a polygon to this cell and return the corresponding object. If the given list of points does not close,
        pylayout will automatically add the first point to the end of the point list in order to close it.

        :param points: an iterable of points that are the vertices of the polygon.
        :param layer: the layer on which the polygon is created.
        :return: a Polygon object.
        """
        pyl_polygon = self.pyl.addPolygon(self.drawing._to_point_array(points), int(layer))
        return Polygon(pyl_polygon, self.drawing)

    def add_polygon_arc(self, center, inner_radius, outer_radius, layer, start_angle=0, stop_angle=0):
        """
        Add a polygon in the shape of a full or partial annulus to this cell and return the corresponding object. The
        default start and stop angles create an arc that touches itself, forming a full annulus. The angles are taken
        mod 360, so it is not possible to create a polygon that overlaps itself.

        :param center: a point containing the (x, y) coordinates of the circle center.
        :param inner_radius: the inner radius of the arc.
        :param outer_radius: the outer radius of the arc.
        :param layer: the layer on which the arc is created.
        :param start_angle: the start angle, measured counterclockwise from the x-axis.
        :param stop_angle: the stop angle, measured counterclockwise from the x-axis.
        :return: a Polygon object.
        """
        pyl_polygon = self.pyl.addPolygonArc(self.drawing._np_to_pyqt(to_point(center)),
                                             self.drawing.to_database_units(inner_radius),
                                             self.drawing.to_database_units(outer_radius),
                                             float(start_angle), float(stop_angle), int(layer))
        return Polygon(pyl_polygon, self.drawing)

    def add_path(self, points, layer, width=None, cap=None):
        """
        Add a path to this cell and return the corresponding object. A path may be closed or open.

        :param points: an iterable of points that are the vertices of the path.
        :param layer: the layer on which the path is created.
        :param width: the width of the path.
        :param cap: the cap style of the path; the default of None will create a path with the current default cap.
        :return: a Path object.
        """
        pyl_path = self.pyl.addPath(self.drawing._to_point_array(points), int(layer))
        path = Path(pyl_path, self.drawing)
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
        pyl_text = self.pyl.addText(int(layer), self.drawing._np_to_pyqt(to_point(origin)), str(text))
        text_ = Text(pyl_text, self.drawing)
        if height is not None:
            text_.height = height
        return text_


class Element(object):

    def __init__(self, pyl_element, drawing):
        self.pyl = pyl_element
        self.drawing = drawing

    @property
    def points(self):
        return self.drawing._to_list_of_np_arrays(self.pyl.getPoints())

    @points.setter
    def points(self, points):
        self.pyl.setPoints(self.drawing._to_point_array(points))

    @property
    def data_type(self):
        return self.pyl.getDatatype()

    @data_type.setter
    def data_type(self, data_type):
        self.pyl.setDatatype(int(data_type))

    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, self.points)

    @property
    def angle(self):
        return self.pyl.getTrans().getAngle()

    @angle.setter
    def angle(self, angle):
        transformation = self.pyl.getTrans()
        # Bizarrely, strans.rotate(angle) rotates by -angle; these lines rotate to zero then to the desired angle.
        transformation.rotate(transformation.getAngle())
        transformation.rotate(-angle)
        self.pyl.setTrans(transformation)

    @property
    def scale(self):
        """
        The scale of the transformation. The returned value is always positive. However, setting a negative scale will
        produce a rotation by 180 degrees along with a scaling by the absolute value of the given scale.
        """
        return self.pyl.getTrans().getScale()

    @scale.setter
    def scale(self, scale):
        transformation = self.pyl.getTrans()
        transformation.scale(scale / transformation.getScale())
        self.pyl.setTrans(transformation)

    @property
    def mirror_x(self):
        return self.pyl.getTrans().getMirror_x()

    @mirror_x.setter
    def mirror_x(self, mirror):
        transformation = self.pyl.getTrans()
        if bool(mirror) ^ transformation.getMirror_x():
            transformation.toggleMirror_x()
        self.pyl.setTrans(transformation)

    def reset_transformation(self):
        transformation = self.pyl.getTrans()
        transformation.reset()
        self.pyl.setTrans(transformation)


class LayerElement(Element):
    """
    This class is identical to Element except that it adds a layer property for Elements that exist on a single
    layer, which is all of them except for the Cellref and CellrefArray classes.
    """

    @property
    def layer(self):
        return self.pyl.layerNum

    @layer.setter
    def layer(self, layer):
        self.pyl.layerNum = int(layer)


class CellElement(Element):
    """
    This class adds a cell attribute to Element.
    """

    def __init__(self, pyl_element, drawing):
        super(CellElement, self).__init__(pyl_element, drawing)
        self.cell = Cell(pyl_element.depend(), drawing)


class Cellref(CellElement):

    def __str__(self):
        return 'Cell {} at ({:.3f}, {:.3f})'.format(self.cell.name, self.origin[0], self.origin[1])

    @property
    def origin(self):
        return self.points[0]

    @origin.setter
    def origin(self, origin):
        self.points = [to_point(origin)]


class CellrefArray(CellElement):

    def __str__(self):
        return 'Cell {}: {} {} by {}'.format(self.cell.name, self.points, self.repeat_x, self.repeat_y)

    @staticmethod
    def _to_pylayout(points):
        origin, step_x, step_y = points
        return [origin, step_x + origin, step_y + origin]

    @staticmethod
    def _from_pylayout(points):
        origin, pyl_x, pyl_y = points
        return [origin, pyl_x - origin, pyl_y - origin]

    @property
    def points(self):
        return self._from_pylayout(self.drawing._to_list_of_np_arrays(self.pyl.getPoints()))
    
    @points.setter
    def points(self, points):
        self.pyl.setPoints(self.drawing._to_point_array(self._to_pylayout(points)))

    @property
    def origin(self):
        return self.points[0]

    @origin.setter
    def origin(self, origin):
        self.points = [to_point(origin), self.points[1], self.points[2]]

    @property
    def step_x(self):
        return self.points[1]

    @step_x.setter
    def step_x(self, step_x):
        self.points = [self.points[0], to_point(step_x), self.points[2]]

    @property
    def step_y(self):
        return self.points[2]

    @step_y.setter
    def step_y(self, step_y):
        self.points = [self.points[0], self.points[1], to_point(step_y)]

    @property
    def repeat_x(self):
        return self.pyl.getNx()

    @repeat_x.setter
    def repeat_x(self, repeat):
        self.pyl.setNx(int(repeat))

    @property
    def repeat_y(self):
        return self.pyl.getNy()

    @repeat_y.setter
    def repeat_y(self, repeat):
        self.pyl.setNy(int(repeat))


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

    @property
    def perimeter(self):
        return 2 * self.width + 2 * self.height


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
        return np.sqrt(np.sum((self.points[0] - self.center) ** 2))

    @property
    def perimeter(self):
        """
        Return the perimeter in user units.

        For a Polygon the first and last point are always the same.

        :return: the perimeter calculated from the element points
        """
        x, y = np.vstack(self.points).T
        return np.sum(np.hypot(np.diff(x), np.diff(y)))


class Path(LayerElement):

    @property
    def width(self):
        return self.pyl.getWidth()

    @width.setter
    def width(self, width):
        self.pyl.setWidth(self.drawing.to_database_units(width))

    @property
    def cap(self):
        return self.pyl.getCap()

    @cap.setter
    def cap(self, cap):
        self.pyl.setCap(int(cap))

    @property
    def length(self):
        """
        Return the length of the path in user units, not including the caps.

        :return: the path length
        """
        x, y = np.vstack(self.points).T
        return np.sum(np.hypot(np.diff(x), np.diff(y)))


class Polygon(LayerElement):

    @property
    def perimeter(self):
        """
        Return the perimeter in user units.

        For a Polygon the first and last point are always the same.

        :return: the perimeter calculated from the element points
        """
        x, y = np.vstack(self.points).T
        return np.sum(np.hypot(np.diff(x), np.diff(y)))


class Text(LayerElement):

    def __str__(self):
        return 'Text "{}" at ({:.3f}, {:.3f})'.format(self.text, self.origin[0], self.origin[1])

    @property
    def text(self):
        return self.pyl.getName().toAscii().data()

    @text.setter
    def text(self, text):
        self.pyl.setName(text)

    @property
    def height(self):
        return self.drawing.from_database_units(self.pyl.getWidth())

    @height.setter
    def height(self, height):
        self.pyl.setWidth(self.drawing.to_database_units(height))

    @property
    def origin(self):
        return self.points[0]

    @origin.setter
    def origin(self, origin):
        self.points = [to_point(origin)]
