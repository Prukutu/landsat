import landsat

# You just need to specify the location of your landsat scenes (with the
# approprate bands.
lsat = landsat.Landsat5(datadir)

lst = lsat.estimateLST() - 273.15

bounds = range(30, 45, 2)
