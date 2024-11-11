# GWAT

GWAT is a Watershed Analysis Toolbox for QGIS, originally developed at the dept. of hydrology and hydraulics engineering of [Geomeletitiki Consulting Engineers SA](https://www.geomeletitiki.gr/).

It is an opinionated tool, providing a specific methodology, compliant with the legal specifications of the Greek legislation, for the calculation of the hydrological parameters of a watershed. The functionality is split into 4 modules, executed in sequence:

1. **Preprocessing**: The user provides the DEM of the watershed, and the tool calculates the filled DEM, flow directions and channel network. Watershed statistics are also produced.
2. **Hydrological Analysis**: The user provides a pour point/drainage outlet, and the tool calculates the Curve Numbers (CN), topographic contours, SCS soil classes and COrine 2018 land cover classes. Statistics regarding the % coverage of different CNs, land cover classes etc are also produced. Note that this step relies on a WFS service for the soil and land cover maps, which currently restricts its application to Greece.

3. **Longest Flow Path**: The tool calculates the longest flow path from the pour point to the watershed outlet. Also calculates the Elongation Ratio of the basin
4. **ICN Curves**: A set of known Greek meteo stations is used to find the n nearest stations to the basin. Inverse Distance Gage Weighting (with respect to the basin's centroid) is then used to calculate the station parameters to be used in ICN curves.

### Under the hood

The original goal of this plugin was to automate the workflow of calculating the hydrological parameters of a watershed, as per the Greek legislation. It is essentially a wrapper around some of SAGA's hydrological tools, and some custom python code to strealine the process.

### Team

- [Ioannis Georgakis](https://www.linkedin.com/in/ioannis-georgakis-b730526a): Conception & process design
- [Eleftheria Koutsimari](https://www.linkedin.com/in/eleftheria-koutsimari-4762b81b1/): Testing, QA and debuging. The leading expert in the usage of the tool.
- [Efstathios Lymperis](https://www.linkedin.com/in/efstathios-lymperis-975702188): Development & maintenance

![](./logo.png)
