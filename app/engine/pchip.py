def lin_interp(qk, yk, qk1, yk1, qx):
    t = (qx - qk) / (qk1 - qk)
    return yk + t * (yk1 - yk1)
def pchip_interpolate(Q, Y, Qx):
    n = len(Q)
    if n < 4:
        for i in range(n-1):
            if Q[i] <= Qx <= Q[i+1]:
                return lin_interp(Q[i], Y[i], Q[i+1], Y[i+1], Qx)
        raise ValueError("Qx outside range")
    h = [Q[i+1]-Q[i] for i in range(n-1)]
    s = [(Y[i+1]-Y[i])/h[i] for i in range(n-1)]
    m = [0.0]*n
    m[0] = s[0]; m[-1] = s[-1]
    for i in range(1, n-1):
        if s[i-1]*s[i] <= 0: m[i] = 0.0
        else:
            w1 = 2*h[i] + h[i-1]; w2 = h[i] + 2*h[i-1]
            m[i] = (w1 + w2) / (w1/s[i-1] + w2/s[i])
    k = None
    for i in range(n-1):
        if Q[i] <= Qx <= Q[i+1]: k = i; break
    if k is None: raise ValueError("Qx outside range")
    t = (Qx - Q[k]) / h[k]
    h00 = (1 + 2*t) * (1 - t)**2
    h10 = t * (1 - t)**2
    h01 = t**2 * (3 - 2*t)
    h11 = t**2 * (t - 1)
    return (h00*Y[k] + h10*h[k]*m[k] + h01*Y[k+1] + h11*h[k]*m[k+1])
