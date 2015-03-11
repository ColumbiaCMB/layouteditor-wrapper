"""
This module is an interface to pylayout.

The goal is to make design simpler.

Conventions:
- variables representing pylayout classes always have pl_ as a prefix.
- functions expect user units and not database units, unlike the pylayout classes.
- only the corresponding class should deal with the pylayout class: for example, a library.Cell class has an instance of
  a pylayout.cell instance called pl_cell; other classes should interface only with the Cell class.
"""
from __future__ import division
import pylayout


class Drawing(object):

    def __init__(self, pl_drawing, expect_user_unit=True):
        """
        :param drawing: :param expect_database_unit: a boolean that determines whether all values input to classes in
        this module are expected to be in user units or database units.
        :return: a Drawing instance.
        """
        self.pl_drawing = pl_drawing
        self.expect_user_unit = expect_user_unit

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

    def scale(self, value):
        if self.expect_user_unit:
            return int(round(value / self.user_unit))
        else:
            return int(round(value))

    @property
    def cells(self):
        return self._parse_cell_linked_list(self.pl_drawing.firstCell, [])

    def _parse_cell_linked_list(self, current, cell_list):
        if current is not None:
            cell_list.append(Cell(current.thisCell, self))
            return self._parse_cell_linked_list(current.nextCell, cell_list)
        else:
            return cell_list

    def point(self, x, y):
        """
        Create a point without adding the point to the drawing.

        :param x: the x-coordinate of the point in either user units or database units; see __init__().
        :param y: the y-coordinate of the point in user units or database units; see __init__().
        :return: a PyQt4.QtCore.QPoint instance that contains the given coordinates in integer database units.
        """
        return pylayout.point(self.scale(x), self.scale(y))

    def point_array(self, points):
        p = pylayout.pointArray(len(points))
        for i, (x, y) in enumerate(points):
            p.setPoint(i, self.point(x, y))
        return p

    def add_cell(self, name=None):
        pl_cell = self.pl_drawing.addCell().thisCell
        if name is not None:
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
        self.pl_cell.cellName = str(name)

    @property
    def elements(self):
        return self._parse_element_linked_list(self.pl_cell.firstElement, [])

    def _parse_element_linked_list(self, current, element_list):
        if current is not None:
            element_list.append(instantiate_element(current.thisElement, self.drawing))
            return self._parse_element_linked_list(current.nextElement, element_list)
        else:
            return element_list

    def __str__(self):
        return 'Cell {}: {}'.format(self.name, [str(e) for e in self.elements])

    def add_cell(self, cell, x, y):
        pl_cell = self.pl_cell.addCellref(cell.pl_cell, self.drawing.point(x, y))
        return Cellref(pl_cell, self.drawing)

    def add_cell_array(self, cell, x, y, dx, dy, nx, ny):
        origin = self.drawing.point(x, y)
        offset = self.drawing.point(x + dx, y + dy)
        pl_cell_array = self.pl_cell.addCellrefArray(cell.pl_cell, origin, offset, int(nx), int(ny))
        return CellrefArray(pl_cell_array, self.drawing)

    def add_box(self, x, y, width, height, layer):
        pl_box = self.pl_cell.addBox(self.drawing.scale(x),
                                     self.drawing.scale(y),
                                     self.drawing.scale(width),
                                     self.drawing.scale(height),
                                     int(layer))
        return Box(pl_box, self.drawing)

    def add_circle(self, x, y, radius, layer, number_of_points=0):
        pl_circle = self.pl_cell.addCircle(int(layer), self.drawing.point(x, y), self.drawing.scale(radius),
                                           int(number_of_points))
        return Circle(pl_circle, self.drawing)

    def add_polygon(self, points, layer):
        pl_polygon = self.pl_cell.addPolygon(self.drawing.point_array(points), int(layer))
        return Polygon(pl_polygon, self.drawing)

    def add_path(self, points, layer, width=None):
        pl_path = self.pl_cell.addPath(self.drawing.point_array(points), int(layer))
        path = Path(pl_path, self.drawing)
        if width is not None:
            path.width = width
        return path

    def add_text(self, x, y, text, layer, height=None):
        pl_text = self.pl_cell.addText(int(layer), self.drawing.point(x, y), str(text))
        text_ = Text(pl_text, self.drawing)
        if height is not None:
            text_.height = height
        return text_

# There must be an easier way to do this...
def instantiate_element(pl_element, drawing):
    if pl_element.isBox():
        return Box(pl_element, drawing)
    elif pl_element.isCellref():
        return Cellref(pl_element, drawing)
    elif pl_element.isCellrefArray():
        return CellrefArray(pl_element, drawing)
    elif pl_element.isCircle():
        return Circle(pl_element, drawing)
    elif pl_element.isPath():
        return Path(pl_element, drawing)
    elif pl_element.isPolygon():
        return Polygon(pl_element, drawing)
    elif pl_element.isText():
        return Text(pl_element, drawing)
    else:
        raise LibraryError("Unknown pylayout element.")


class Element(object):
    def __init__(self, pl_element, drawing):
        self.pl_element = pl_element
        self.drawing = drawing

    """
    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, self.__hash__())
    """


class Cellref(Element):
    def __init__(self, pl_element, drawing):
        super(Cellref, self).__init__(pl_element, drawing)
        self.cell = Cell(pl_element.depend(), drawing)

    def __str__(self):
        return str(self.cell)


class CellrefArray(Element):
    def __init__(self, pl_element, drawing):
        super(CellrefArray, self).__init__(pl_element, drawing)
        self.cell = Cell(pl_element.depend(), drawing)

    def __str__(self):
        return str(self.cell)


class Box(Element):
    pass


class Circle(Element):
    pass


class Path(Element):

    @property
    def width(self):
        return self.pl_element.getWidth()

    @width.setter
    def width(self, width):
        self.pl_element.setWidth(self.drawing.scale(width))


class Polygon(Element):
    pass


class Text(Element):
    @property
    def text(self):
        return self.pl_element.getName().toAscii().data()

    @text.setter
    def text(self, text):
        self.pl_element.setName(text)

    @property
    def height(self):
        return self.pl_element.getWidth()

    @height.setter
    def height(self, height):
        self.pl_element.setWidth(self.drawing.scale(height))

    def __str__(self):
        return 'Text: {}'.format(self.text)


class LibraryError(Exception):
    pass
