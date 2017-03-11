__author__ = 'jason'

class TrendLine():
    def __init__(self, xlist, ylist):
        self.xlist = xlist
        self.ylist = ylist

        if len(self.xlist) != len(self.ylist):
            raise IndexError
        self.n = len(x)

        sigma_x = 0
        for i in range(0, self.n):
            sigma_x += self.xlist[i]

        sigma_xx = 0
        for i in range(0, self.n):
            sigma_xx += self.xlist[i]*self.xlist[i]

        sigma_x2 = sigma_x*sigma_x

        sigma_xy = 0
        for i in range(0, self.n):
            sigma_xy += self.xlist[i]*self.ylist[i]

        sigma_y = 0
        for i in range(0, self.n):
            sigma_y += self.ylist[i]

        # α = (n * Σ(xy) - Σx * Σy) / (n * Σ(x^2) - (Σx)^2)
        self.gradient = (self.n*sigma_xy-sigma_x*sigma_y) / \
                        (self.n*sigma_xx-sigma_x2)

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
