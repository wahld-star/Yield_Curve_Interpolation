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
- Monotone Convex Interpolation with positivity enforcement

## Upcoming Features:
- Swap builder (~1-2 weeks)
- Custom Input Curve Builder (~2-3 weeks)

## Features: 
- Interpolation Method Selection
- Select Historical Date via UST daily par curve rates
- Enforce positivty; default to yes
- Amelioration
    - Set lambda; default to .20
- Target Rate
- Historical Curve Comparison
- Export to jpeg

## Known Bugs:
    - Error handling dates
    - Using a different method to chart a second curve