__author__ = 'jason'

class TrendLine():
    def __init__(self, xlist, ylist):
        self.xlist = xlist
        self.ylist = ylist

        if len(self.xlist) != len(self.ylist):
            raise IndexError
        if len(self.xlist) == 0:
            self.n = 0
            self.offset = 0
            self.gradient = 0
            return None

        self.n = len(self.xlist)

        sigma_x = 0.0
        sigma_xx = 0.0
        sigma_xy = 0.0
        sigma_y = 0.0
        for i in range(0, self.n):
            sigma_x += float(self.xlist[i])
            sigma_xx += float(self.xlist[i])*float(self.xlist[i])
            sigma_xy += float(self.xlist[i])*float(self.ylist[i])
            sigma_y += float(self.ylist[i])

        sigma_x2 = float(sigma_x)*float(sigma_x)

        # α = (n * Σ(xy) - Σx * Σy) / (n * Σ(x^2) - (Σx)^2)
        if sigma_xx != sigma_x2:
            self.gradient = (self.n*sigma_xy-sigma_x*sigma_y) / \
                            (self.n*sigma_xx-sigma_x2)
        else:
            self.gradient = 0

        # β = (Σy - α * Σx)/n
        self.offset = (sigma_y-self.gradient*sigma_x)/self.n

    # y = α * x + β
    def get_trend_point(self, xvalue):
        return self.gradient*xvalue + self.offset


if __name__ == "__main__":
    x = range(0, 10)
    y = range(0, 20, 2)
    trendline = TrendLine(asx_code="cba", xlist=x, ylist=y)
    print(trendline.get_trend_point(15))
