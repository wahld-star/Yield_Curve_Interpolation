### This repository provides Yield Curve Construction using various interpolation methods

This repository allows users to construct Yield Curves using various interpolation methods.
Data is retrieved via the US Department of Treasury historical treasury yield xml feed.
https://home.treasury.gov/sites/default/files/interest-rates/yield.xml

### Current Update
This repository is actively a work in progress with update coming daily. The repository is a learning project for my own fun and
is almost certainly riddled with bugs. 

The following are currently completed:
- US Treasury XML feed pull 
- Straight Line Interpolation
- Cubic Spline Interpolation



## optionality: 
    - positivty? default to yes
    - amelioration? default to no 
        - Set lambda; default to .20
    - Rates to pull??? *may exclude*
    - target rate
    - number of points; default to 1000