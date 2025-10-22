from math import sqrt, asin, degrees, radians, cos, sin
from numpy import vectorize, linspace
from collections import namedtuple
from lion.logger.exception_logger import log_exception
from lion.orm.location import Location


class Arrow():

    def __init__(self):

        self.__dict_footprint = Location.to_dict()
        self.dict_tour_circles = {}

    def get_arrow_points(self, loc_codes=[], movements=[]):

        self.list_tour_polylines = {}

        try:

            for i in range(len(loc_codes) - 1):

                lat1 = float(self.__dict_footprint[loc_codes[i]]['latitude'])
                lon1 = float(self.__dict_footprint[loc_codes[i]]['longitude'])
                lat2 = float(
                    self.__dict_footprint[loc_codes[i + 1]]['latitude'])
                lon2 = float(
                    self.__dict_footprint[loc_codes[i + 1]]['longitude'])

                self.movement = movements[i]

                self.list_tour_polylines.update({self.movement: {}})

                ky1 = str(loc_codes[i] + '->' + loc_codes[i+1])

                if ky1 not in self.dict_tour_circles.keys():

                    radius = sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 2
                    c1, c2 = self.circles_from_p1p2r(
                        p1=[lon1, lat1], p2=[lon2, lat2], r=radius)

                    # if (c1 is None) or (c2 is None):
                    #     update_log(message='No circle was found from {} to {}'.format(loc_codes[i], loc_codes[i + 1]),
                    #                module_name='arrow.py/get_arrow_points')

                    self.dict_tour_circles.update({ky1: c1})

                    ky2 = str(loc_codes[i+1] + '->' + loc_codes[i])
                    self.dict_tour_circles.update({ky2: c2})

                __get_curve_points_ok = self.get_curve_points(point1=[lon1, lat1], point2=[lon2, lat2], n=100,
                                                              circle=self.dict_tour_circles[ky1])

                if not __get_curve_points_ok:
                    return {}

            return self.list_tour_polylines

        except Exception:
            log_exception(popup=False)

            return []

    def arrow(self, lat1, lon1, lat2, lon2,
              ratio=0.05,
              Arrow_height=0,
              alpha=45):

        try:
            x1 = lon1
            y1 = lat1
            x2_end = lon2
            y2_end = lat2

            # The arrow will be placed in the middle of the line
            x2 = (x1 + x2_end) / 2
            y2 = (y1 + y2_end) / 2

            D = sqrt((y2 - y1)**2 + (x2 - x1)**2)

            if Arrow_height == 0:

                if Arrow_height + ratio == 0:
                    raise ValueError(
                        'The height of the arrow could not be determined.')

                Arrow_height = ratio * D

            if D > 0:

                alpha_1 = self.asin(abs(y2-y1)/D)

                if alpha_1 > 45:
                    alpha = (90 - alpha_1)*2/3
                else:
                    alpha = alpha_1 * 2/3

                Arrow_leg = Arrow_height/self.cos(alpha)

                a0 = 90 - alpha_1 - alpha

                tx0 = Arrow_leg * self.sin(a0)
                xx0 = x2 - (x2 > x1) * tx0 + (x2 < x1) * tx0

                ty0 = Arrow_leg * self.cos(a0)
                yy0 = y2 - (y2 > y1) * ty0 + (y2 < y1) * ty0

                a1 = alpha_1 - alpha
                tx0 = Arrow_leg * self.cos(a1)
                xx1 = x2 - (x2 > x1) * tx0 + (x2 < x1) * tx0

                ty0 = Arrow_leg * self.sin(a1)
                yy1 = y2 - (y2 > y1) * ty0 + (y2 < y1) * ty0

                self.list_tour_polylines[self.movement].update(
                    {'arrow': [[yy0, xx0], [y2, x2], [yy1, xx1]]})

        except Exception:
            log_exception(popup=False)

    def get_curve_points(self, point1, point2, n=0, circle=None):

        if circle is None:
            # update_log(message='No circle was found.',
            #            module_name='arrow/get_curve_points()')
            return False

        __get_curve_points_ok = True
        try:

            xmax = max(point1[0], point2[0])
            xmin = min(point1[0], point2[0])
            ymax = max(point1[1], point2[1])
            ymin = min(point1[1], point2[1])

            if abs(ymin - ymax) <= 0.05 and abs(xmin - xmax) <= 0.05:
                n = 0

            if (n == 0) or (circle is None):

                self.list_tour_polylines[self.movement].update(
                    {'points': [[point1[1], point1[0]], [point2[1], point2[0]]]})
                self.arrow(lat1=point1[1], lon1=point1[0],
                           lat2=point2[1], lon2=point2[0], ratio=0.05)

                return

            def get_c_y(x):

                if x == point1[0]:
                    return point1[1]
                elif x == point2[0]:
                    return point2[1]

                y1 = circle.y + sqrt(circle.r**2 - (x - circle.x)**2)
                y2 = circle.y - sqrt(circle.r**2 - (x - circle.x)**2)

                if ymin <= y1 <= ymax:
                    return y1
                elif ymin <= y2 <= ymax:
                    return y2
                elif abs(ymin - ymax) <= 0.05:

                    if abs(y1 - ymax) < abs(y2 - ymax):
                        return y1
                    else:
                        return y2

                if abs(y1 - ymax) < abs(y2 - ymax):
                    return y1
                else:
                    return y2

            def get_c_x(y):

                if y == point1[1]:
                    return point1[0]
                elif y == point2[1]:
                    return point2[0]

                x1 = circle.x + sqrt(circle.r**2 - (y - circle.y)**2)
                x2 = circle.x - sqrt(circle.r**2 - (y - circle.y)**2)

                if xmin <= x1 <= xmax:
                    return x1
                elif xmin <= x2 <= xmax:
                    return x2
                elif abs(xmin - xmax) <= 0.05:

                    if abs(x1 - xmax) < abs(x2 - xmax):
                        return x1
                    else:
                        return x2

                if abs(x1 - xmax) < abs(x2 - xmax):
                    return x1
                else:
                    return x2

            vec_get_c_y = vectorize(get_c_y)
            vec_get_c_x = vectorize(get_c_x)

            if abs(xmin - xmax) <= 0.1:

                y_array = linspace(
                    min(point1[1], point2[1]), max(point1[1], point2[1]), n)
                if point1[1] > point2[1]:
                    y_array = list(reversed(y_array))

                x_array = vec_get_c_x(y_array)
                points = [[y_array[i], x_array[i]]
                          for i in range(len(x_array))]
            else:

                x_array = linspace(
                    min(point1[0], point2[0]), max(point1[0], point2[0]), n)
                if point1[0] > point2[0]:
                    x_array = list(reversed(x_array))

                y_array = vec_get_c_y(x_array)
                points = [[y_array[i], x_array[i]]
                          for i in range(len(x_array))]

            self.list_tour_polylines[self.movement].update({'points': points})
            D = sqrt((point2[1] - point1[1])**2 +
                     (point2[0] - point1[0])**2)

            mdl_point = int(len(points)/2)
            p1 = points[mdl_point]
            p2 = points[mdl_point + 1]
            self.arrow(lat1=p1[0], lon1=p1[1], lat2=p2[0],
                       lon2=p2[1], Arrow_height=0.05*D)

        except Exception:
            log_exception(popup=False, remarks='Error when designing arrow.')
            return False

        return __get_curve_points_ok

    def circles_from_p1p2r(self, p1, p2, r):

        Cir = namedtuple('Circle', 'x, y, r')

        try:
            'Following explanation at http://mathforum.org/library/drmath/view/53027.html'
            if r == 0.0:
                return None, None
                # raise ValueError('radius of zero')

            (x1, y1), (x2, y2) = p1, p2
            if p1 == p2:
                raise ValueError(
                    'coincident points gives infinite number of Circles')
            # delta x, delta y between points
            dx, dy = x2 - x1, y2 - y1
            # dist between points
            q = sqrt(dx**2 + dy**2)
            if q > 2.0 * r:
                raise ValueError('separation of points > diameter')
            # halfway point
            x3, y3 = (x1+x2)/2, (y1+y2)/2
            # distance along the mirror line
            d = sqrt(r**2-(q/2)**2)

            # ---------------------------------------
            # slope of line going through p1 and p2 is dy/dx
            # which means that slope of a line that is perpendicular to the line above would be
            slope = -1 * dx/dy

            # constant of the perpendicular line
            const = y3 - slope * x3
            # To find the center of the circle, we have to find a point on the perpendicular
            # line which is in d distance from (x3, y3)
            # to this end, we have to solve the following quadratic eq
            # (1 + slope^2) x^2 + (2*slope * (const-y3) - 2 * x3) * x = d^2 - x3^2 - (const - y3)^2
            # See here https://www.mathpapa.com/quadratic-formula/
            # X1 = -b + sqrt(b^2 - 4*a*c)
            # X2 = -b - sqrt(b^2 - 4*a*c)

            a = 1 + slope**2
            b = 2 * ((const - y3) * slope - x3)
            c = x3**2 + (const - y3)**2 - d**2

            circle_X1 = (-1 * b + sqrt(b**2 - 4 * a * c))/(2 * a)
            circle_X2 = (-1 * b - sqrt(b**2 - 4 * a * c))/(2 * a)

            circle_Y1 = slope * circle_X1 + const
            circle_Y2 = slope * circle_X2 + const

            # ----------------------------------------
            # One answer
            c1 = Cir(x=circle_X1,
                     y=circle_Y1,
                     r=abs(r))

            # The other answer
            c2 = Cir(x=circle_X2,
                     y=circle_Y2,
                     r=abs(r))

        except Exception:
            log_exception(popup=False)
            return None, None

        return c1, c2

    def sin(self, x_degrees):
        try:
            return sin(radians(x_degrees))
        except Exception:
            log_exception(popup=False)
            return None

    def asin(self, x):
        try:
            return degrees(asin(x))
        except Exception:
            log_exception(popup=False)
            return None

    def cos(self, x_degrees):
        try:
            return cos(radians(x_degrees))
        except Exception:
            log_exception(popup=False)
            return None
