def scale_speed(point, N1: float, N2: float):
    r = N2 / N1
    Q, H, P = point
    return (Q*r, H*r*r, P*r*r*r)
def scale_diameter(point, D1: float, D2: float):
    r = D2 / D1
    Q, H, P = point
    return (Q*r, H*r*r, P*r*r*r)
