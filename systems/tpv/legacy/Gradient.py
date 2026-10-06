from TPVconfig import TPVconfig
import numpy as np
from Irradiance import IrradianceModel

class GradientModel:
    def __init__(self, config: TPVconfig):
        self.cfg = config
        # self.temp = self.cfg.temp
        # self.d = self.cfg.d
        # self.width = self.cfg.width_e
        # self.height = self.cfg.height_e
        self.x_grid = self.cfg.x_grid
        self.y_grid = self.cfg.y_grid
        self.x_mesh, self.y_mesh = np.meshgrid(self.x_grid, self.y_grid)

        # self.dA_e = self.cfg.dA_e
        self.IrModel = IrradianceModel(config)
        self.irradiance_vect = np.vectorize(self.IrModel.calculate_Irradiance)

    def _calculate_gradient(self):

        z_matrix = self.irradiance_vect(self.x_mesh, self.y_mesh)
        gy , gx = np.gradient(z_matrix,self.cfg.dx, self.cfg.dy)
        self.gy = gy
        self.gx = gx
        return gy, gx
    
    def _second_derivative(self):
        dxy , dxx = np.gradient(self.gx, self.cfg.dy, self.cfg.dx)

        dyy , _ = np.gradient(self.gy, self.y_mesh, self.x_mesh)
        self.dyy = dyy
        self.dxx = dxx
        self.dxy = dxy
        return dxx,dyy,dxy
    
    def find_hotspot(self):
        Hessian_det = (self.dxx * self.dyy) - (self.dxy**2)

        local_min = np.where((Hessian_det > 0) & (self.dxx > 0 ))
        local_max = np.where((Hessian_det > 0) &(self.dxx < 0))
        saddle_points = np.where(Hessian_det < 0 )
        return local_max
    

## ======================================================================================================
# Guard

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from TPVconfig import TPVconfig

    cfg = TPVconfig(temp=2000, material_name="blackbody",
                    d=0.1, width_e=0.05, height_e=0.05, x_e=0, y_e=0,
                    xnum=40, ynum=40)
    model = GradientModel(cfg)
    gy, gx = model._calculate_gradient()

    I_vect = np.vectorize(model.IrModel.calculate_Irradiance)
    Z = I_vect(model.x_mesh, model.y_mesh)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # --- Plot 1: Contour + Gradient quiver ---
    ax1 = axes[0]
    c = ax1.contourf(model.x_mesh * 100, model.y_mesh * 100, Z / 1000,
                     levels=20, cmap='inferno')
    plt.colorbar(c, ax=ax1, label="I (kW/m²)")
    skip = 3
    ax1.quiver(model.x_mesh[::skip, ::skip] * 100,
               model.y_mesh[::skip, ::skip] * 100,
               gx[::skip, ::skip], gy[::skip, ::skip],
               color='white', alpha=0.8, scale_units='xy')
    ax1.set_xlabel("x (cm)")
    ax1.set_ylabel("y (cm)")
    ax1.set_title("Irradiance Contour + Gradient Field")
    ax1.set_aspect('equal')

    # --- Plot 2: Gradient magnitude vs radial distance ---
    ax2 = axes[1]
    rho = np.sqrt(model.x_mesh**2 + model.y_mesh**2).flatten()
    grad_mag = np.sqrt(gx**2 + gy**2).flatten()
    ax2.scatter(rho * 100, grad_mag, s=1, alpha=0.5, color='coral')
    rho_star = cfg.d / np.sqrt(3)
    ax2.axvline(rho_star * 100, color='green', linestyle='--',
                label=f"ρ* = d/√3 = {rho_star*100:.2f} cm")
    ax2.set_xlabel("ρ (cm)")
    ax2.set_ylabel("|∇I| (W/m³)")
    ax2.set_title("Gradient Magnitude vs Radial Distance")
    ax2.legend()

    plt.tight_layout()
    plt.savefig("plots/gradient_quiver_and_magnitude.png", dpi=150)
    plt.show()

    # --- Hotspot ---
    center_idx = np.unravel_index(np.argmax(Z), Z.shape)
    print(f"\nHot spot at grid index {center_idx}")
    print(f"Position: ({model.x_mesh[center_idx]*100:.2f}, {model.y_mesh[center_idx]*100:.2f}) cm")
    print(f"Peak irradiance: {Z[center_idx]/1000:.2f} kW/m²")