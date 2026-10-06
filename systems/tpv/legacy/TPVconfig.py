from dataclasses import dataclass, field
import numpy as np

@dataclass
class TPVconfig:
    """Configuration: constants, geometry, material properties"""

    # === Inputs (required — no defaults) ===
    material_name: str
    temp: float
    d: float
    width_e: float
    height_e: float
    x_e: float
    y_e: float

    # === Optional inputs ===
    xnum: int = 50
    ynum: int = 50
    lambda_min: float = 100e-9
    lambda_max: float = 5e-6

    # === Constants (class variables — not part of __init__) ===
    sigma: float = field(default=5.670373e-8, init=False, repr=False)
    wienConstant: float = field(default=2898, init=False, repr=False)
    h_planck: float = field(default=6.62607015e-34, init=False, repr=False)
    c_light: float = field(default=2.998e8, init=False, repr=False)
    k_boltz: float = field(default=1.38e-23, init=False, repr=False)

    MATERIALS = {
        "silicon":   {"Eg": 1.12, "eps_high": 0.9,  "eps_low": 0.5},
        "germanium": {"Eg": 0.66, "eps_high": 0.85, "eps_low": 0.1},
        "blackbody": {"Eg": 0.0,  "eps_high": 1.0,  "eps_low": 1.0},
    }

    def __post_init__(self):
        self.x_grid = np.linspace(-self.width_e / 2, self.width_e / 2, self.xnum)
        self.y_grid = np.linspace(-self.height_e / 2, self.height_e / 2, self.ynum)
        self.dx = self.width_e / self.xnum
        self.dy = self.height_e / self.ynum
        self.dA_e = self.dx * self.dy