'''
Name : planckSpectrumM1-1.py
Description: planck Spectrum Equation Module 1, submodule 1
Type : Support Function 
Question : "How much radiation does the emitter produce, and at what wavelengths?"
'''

""
import numpy as np
import matplotlib as mpt
from TPVconfig import TPVconfig
import physics_utils
# ##################################################################################
# # Defining Constants in advance




# # 1. Stefan-Boltzmann Law

# def stefBoltz(temp_k, emissivity = 1.0):
#     """
#     Calculates radiant exitance,aka, total radiant heat energy of a uniformly radiant black body as well as non-black body in W/m^2.
#     default emissivity (if black body) = 1.0
#     """

#     # Equation : E = epsilon * sigma * T^4
#     radiant_exitance = emissivity * sigma * (temp_k**4)
#     return radiant_exitance

# # 2. Wien's Displacement Law
# def WienDisp(temp_k = None, peakLambda = None):
#     """
#     shows inverse proportionality between Temp of an object and wavelength of light it emits most intensely
#     """
#     if temp_k is not None:
#         return wienConstant/temp_k
    
#     elif peakLambda is not None:
#         return wienConstant/peakLambda

#     else:
#         return "Please provide either temp_k or peakLambda."
    

# ## Edge Case Handling   
# # 3. Selective Emitter
# def selectiveEmit(energyBandGap, Lambda, eps_high = 0.9, eps_low =0.05):
    
#     lambdaBandGap = (h_planck*c_light)/energyBandGap

#      # Bandgap Energy differs per material
#     # to be further developed using transparency-total blackbody spectrum, thermal equilibrium, and urbach tail absorption coefficient
#     return np.where(Lambda<=lambdaBandGap, eps_high, eps_low )

# # 4. Planck's spectral radiance 

# def totalPower(Lambda, temp_k, material_name="blackbody"):

#     materialProp = MATERIALS.get(material_name.lower(),MATERIALS["blackbody"])
#     energyBandGap = materialProp["Eg"]*1.60218e-19

#     C1 = (2 * h_planck * (c_light**2) ) / (Lambda**5) # first constant 2hc^2/lambda^5
#     phoE = (h_planck * c_light) / Lambda # Photon Energy E = hf, f = c/lambda
#     thermE = k_boltz * temp_k # thermal energy = kT

#     with np.errstate(over = 'ignore'):
#         boltzFactor = np.exp(phoE/thermE) #Planck distribution factor. It’s what gives the blackbody curve its distinct "hill" shape.
    
#         planckSpectral = C1*(1/(boltzFactor -1))


#     emissivity = selectiveEmit(energyBandGap, Lambda, materialProp["eps_high"], materialProp["eps_low"]) # Lambda is a vector or a np array
    
#     radiance = planckSpectral * emissivity

#     return np.trapezoid(radiance,Lambda) 



'''
Output Testing
wavelengths = np.linspace(400e-9, 500e-12, 50)
temp_k = np.linspace(2500, 4000, 50)
radiance = planckSpectral(wavelengths, temp_k)

#print (radiance[:10])'''

# ====================================================================
## Using OOP and Classes
# ====================================================================

class PlanckModel:

    def __init__(self, config: TPVconfig):
        self.cfg = config
        m_name = self.cfg.material_name.lower()
        self.mat = TPVconfig.MATERIALS.get(m_name, TPVconfig.MATERIALS["blackbody"])
        self.h = self.cfg.h_planck
        self.c = self.cfg.c_light
        self.k = self.cfg.k_boltz
        self.temp = self.cfg.temp


    
    def _selective_emit(self, Lambda):
        Eg = self.mat["Eg"]
        Eg = self.mat["Eg"]
        if Eg == 0.0:
            return np.ones_like(Lambda)
        Eg_bg = Eg * (1.602e-19)
        eps_low = self.mat["eps_low"]
        eps_high = self.mat["eps_high"]

        lambda_bg = (self.h * self.c) / Eg_bg

        return np.where(Lambda <= lambda_bg, eps_high, eps_low)
    
    def _calculate_spectral_radiance(self, Lambda: np.ndarray) -> np.ndarray:
        """Returns the y-value of the planck curve with Lambda array values being x values"""
        C1 = ( 2 * self.h * (self.c**2)) / (Lambda**5)
        pE = ( self.h * self.c) / Lambda 
        tE = self.k * self.temp 

        with np.errstate( over = 'ignore'):
            boltzFactor = np.exp(pE/tE)
            planck_raw = C1*(1/(boltzFactor-1))

        emissivity = self._selective_emit(Lambda)

        return planck_raw * emissivity  # this will return an array of radiance values

    def get_total_power(self, Lambda_range: np.ndarray) -> float: 
        
        radiance = self._calculate_spectral_radiance(Lambda_range)

        return np.trapezoid(radiance, Lambda_range)


# =================================================================
# Guard 

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from TPVconfig import TPVconfig

    cfg = TPVconfig(temp=2500, material_name="blackbody",
                    d=0.1, width_e=0.05, height_e=0.05, x_e=0, y_e=0)
    model = PlanckModel(cfg)
    lambdas = np.linspace(cfg.lambda_min, cfg.lambda_max, 500)

    # --- Plot 1: Planck spectra at multiple temperatures ---
    fig, ax = plt.subplots(figsize=(10, 6))
    temps = [1000, 1500, 2000, 2500, 3000]
    for T in temps:
        cfg_t = TPVconfig(temp=T, material_name="blackbody",
                          d=0.1, width_e=0.05, height_e=0.05, x_e=0, y_e=0)
        m = PlanckModel(cfg_t)
        curve = m._calculate_spectral_radiance(lambdas)
        peak_lam = 2898e-6 / T
        ax.plot(lambdas * 1e6, curve, label=f"{T} K")
        ax.axvline(peak_lam * 1e6, linestyle=':', alpha=0.4)

    ax.set_xlabel("Wavelength (μm)")
    ax.set_ylabel("Spectral Radiance (W/m²/sr/m)")
    ax.set_title("Planck Spectrum — Blackbody at Multiple Temperatures")
    ax.legend()
    ax.set_xlim(0, 5)
    plt.tight_layout()
    plt.savefig("plots/planck_spectra.png", dpi=150)
    plt.show()

    # --- Validation: Stefan-Boltzmann ---
    from physics_utils import radiant_exitance
    print("\n--- Stefan-Boltzmann Validation ---")
    print(f"{'T (K)':<10} {'Numerical (W/m²)':<20} {'σT⁴ (W/m²)':<20} {'Error %':<10}")
    for T in temps:
        cfg_t = TPVconfig(temp=T, material_name="blackbody",
                          d=0.1, width_e=0.05, height_e=0.05, x_e=0, y_e=0)
        m = PlanckModel(cfg_t)
        numerical = m.get_total_power(lambdas) * np.pi  # hemisphere
        analytical = radiant_exitance(T)
        err = abs(numerical - analytical) / analytical * 100
        print(f"{T:<10} {numerical:<20.2f} {analytical:<20.2f} {err:<10.3f}")