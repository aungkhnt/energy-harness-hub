# Reference manifest

Reviewed 2026-09-15. These sources support the family taxonomy and basic modeling
choices. They do not supply the illustrative scenario parameters or example costs.
No current commercial readiness ranking or market-price dataset has been imported.

| Source | Used for | Limitation |
|---|---|---|
| [EIA: How electricity is generated](https://www.eia.gov/energyexplained/electricity/how-electricity-is-generated.php) | Broad generation and conversion families; storage distinction | Not evidence for every catalog archetype |
| [DOE: Marine energy basics](https://www.energy.gov/cmei/water/marine-energy-basics) | Wave, tidal/current, ocean thermal families | Not local resource or project economics |
| [DOE: How hydropower works](https://www.energy.gov/cmei/water/how-hydropower-works) | Head and flow as the hydraulic resource | No site-specific input data |
| [DOE: Types of hydropower turbines](https://www.energy.gov/cmei/water/types-hydropower-turbines) | Head/flow and distinction from kinetic turbines | No turbine curve calibration |
| [DOE: Fuel cell basics](https://www.energy.gov/cmei/fuels/fuel-cell-basics) | Fueled electrochemical conversion | Does not establish upstream hydrogen costs |
| [NASA: Radioisotope technology overview](https://science.nasa.gov/planetary-science/programs/radioisotope-power-systems/overview/) | Radioactive decay heat and thermoelectric conversion | No imported mass, cost or lifetime data |
| [Sandia PVPMC: Single-diode equivalent circuits](https://pvpmc.sandia.gov/modeling-guide/2-dc-module-iv/single-diode-equivalent-circuit-models/) | Cell equivalent-circuit equation | Our ideal limiting case is not a calibrated TPV device |
| [NIST: Spectroradiometry of sources](https://www.nist.gov/programs-projects/spectroradiometry-sources) | Blackbody spectral radiance and Planck law context | Not validation of our implementation |

The finite-area radiation kernel is the diffuse view-factor integrand specialized
to parallel planes. Its implementation is checked by reciprocity, physical bounds,
far-field behavior, and refinement. A source-specific geometry benchmark is still
needed before claiming engineering validation.

Salinity-gradient, thermionic, thermoradiative, mechanical micro-harvesting, RF
harvesting, and waste-heat entries retain an explicit need for specialist references.
Family-level links elsewhere do not verify the feasibility of an individual design.

## Data that still needs sourcing

- A named TPV cell's spectral quantum efficiency, dark current, series/shunt losses,
  temperature behavior, and measured I–V curves under a documented spectrum.
- Spectral emitter properties, cooling requirements, and full source-energy accounting.
- Site resource time series and technology-specific performance curves.
- Regional and dated equipment/material costs, installation, financing and maintenance.
- Supply quantities, material grades, suppliers, lead times, and substitution evidence.
- Deployment status and demonstrated scale for each specific technology archetype.
