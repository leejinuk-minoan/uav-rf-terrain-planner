# Knife-edge Diffraction Formula Foundation

## Purpose
Formula foundation only.
## Current Project Context
Existing DSM LOS/Fresnel scores remain unchanged.
## Formula Scope
Single knife-edge additional diffraction-loss proxy, not a full link budget or real communication prediction.
## Fresnel Radius Contract
`R1=sqrt(lambda*d1*d2/(d1+d2))`.
## Clearance and Height Sign Convention
`clearance=LOS-DSM`; `h=-clearance`.
## Knife-edge Nu Contract
`nu=-sqrt(2)*CF` and equivalent height form.
## Knife-edge Loss Contract
Zero for `nu<=-0.78`; logarithmic approximation otherwise.
## Error Handling
Non-finite and non-positive required inputs raise `FresnelAnalysisError`.
## Non-Goals
No full P.526, Bullington, spherical-earth, multi-obstacle, rounded-ridge, UTD, ITM, scoring, or ranking work.
## Task 032CD Integration Boundary
Task 032CD integrates these helpers into `FresnelAnalysis` as an optional dominant-obstacle diagnostic. The formula helpers remain independent, and the integration does not change scoring, color, ranking, preview, or CLI behavior.
## Public Repository Sensitivity Check
No data artifact.
## Follow-Up Tasks
Any output projection or scoring use requires a separate reviewed task.
