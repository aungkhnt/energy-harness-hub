"""SI reference equations. No material database or empirical calibration is implied."""
import math
from .numerics import bisect

H = 6.62607015e-34
C = 299792458.0
K = 1.380649e-23
Q = 1.602176634e-19
SIGMA = 2 * math.pi**5 * K**4 / (15 * H**3 * C**2)


def positive(name, value, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be a finite number')
    if not math.isfinite(value) or (value < 0 if allow_zero else value <= 0):
        raise ValueError(f'{name} must be finite and {"nonnegative" if allow_zero else "positive"}')
    return value


def fraction(name, value):
    positive(name, value, allow_zero=True)
    if value > 1:
        raise ValueError(f'{name} must be between 0 and 1')
    return value


def integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in [{low}, {high}]')
    return value


def radiance(wavelength_m, temperature_k):
    """Blackbody spectral radiance in W m^-2 sr^-1 m^-1."""
    positive('wavelength_m', wavelength_m)
    positive('temperature_k', temperature_k)
    exponent = H * C / (wavelength_m * K * temperature_k)
    if exponent > 700:
        return 0.0
    return 2 * H * C**2 / wavelength_m**5 / math.expm1(exponent)


def integrate_log(function, lower, upper, intervals=512):
    """Composite Simpson rule after lambda=exp(u); includes the Jacobian."""
    positive('lower', lower)
    positive('upper', upper)
    integer('intervals', intervals, 2, 32768)
    if intervals % 2:
        raise ValueError('Simpson intervals must be even')
    if upper <= lower:
        if upper == lower:
            return 0.0
        raise ValueError('integration upper limit must exceed lower limit')
    lo, hi = math.log(lower), math.log(upper)
    step = (hi - lo) / intervals
    values = []
    for i in range(intervals + 1):
        wavelength = math.exp(lo + i * step)
        weight = 1 if i in (0, intervals) else (4 if i % 2 else 2)
        values.append(weight * function(wavelength) * wavelength)
    return math.fsum(values) * step / 3


def rectangle_coupling(ew, eh, cw, ch, gap, offset_x=0.0, offset_y=0.0, cells=12):
    """Integral cos(theta_e) cos(theta_c)/r^2 dAe dAc, in m^2 sr.

    Parallel, facing, diffuse rectangular emitter/cell in vacuum. Midpoint
    quadrature over both surfaces. Geometry is centered on the receiving cell;
    offsets move the emitter. This is not a near-field electromagnetic model.
    """
    for name, value in [('emitter_width', ew), ('emitter_height', eh),
                        ('cell_width', cw), ('cell_height', ch), ('gap', gap)]:
        positive(name, value)
    for value in (offset_x, offset_y):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('offsets must be finite numbers')
    integer('geometry_cells', cells, 2, 32)
    # Factor the repeated x/y differences without a four-dimensional array.
    xs = [(((i + .5) / cells - .5) * ew + offset_x
           - ((j + .5) / cells - .5) * cw)**2
          for i in range(cells) for j in range(cells)]
    ys = [(((i + .5) / cells - .5) * eh + offset_y
           - ((j + .5) / cells - .5) * ch)**2
          for i in range(cells) for j in range(cells)]
    return math.fsum(gap**2 / (x + y + gap**2)**2 for x in xs for y in ys) * ew * eh * cw * ch / cells**4


def diode_mpp(photocurrent_a, saturation_current_a, temperature_k):
    """Ideal single diode, n=1, Rs=0, Rsh=infinity. Returns MPP and I-V curve."""
    positive('photocurrent_a', photocurrent_a, allow_zero=True)
    positive('saturation_current_a', saturation_current_a)
    positive('temperature_k', temperature_k)
    vt = K * temperature_k / Q
    voc_scaled = math.log1p(photocurrent_a / saturation_current_a)
    # d(VI)/dV = 0 => x + log(1+x) = log(1+Iph/I0).
    solution = bisect(lambda x: x + math.log1p(x) - voc_scaled, 0.0, voc_scaled)
    vmpp = solution.root * vt
    def current(v):
        return photocurrent_a - saturation_current_a * math.expm1(v / vt)
    impp = current(vmpp)
    voc = vt * voc_scaled
    return {'voc_v': voc, 'isc_a': photocurrent_a, 'vmpp_v': vmpp,
            'impp_a': impp, 'dc_power_w': vmpp * impp,
            'iv_curve': [{'voltage_v': voc * i / 100,
                          'current_a': max(0.0, current(voc * i / 100))}
                         for i in range(101)]}
