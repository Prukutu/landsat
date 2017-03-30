import numpy as np
import gdal
import os

# TODO: Comment the code!


class Landsat5:
    """ A class to handle data from a landsat image.

    """

    def __init__(self, datadir):

        filelist = os.listdir(datadir)
        metadata = next(x for x in filelist if x[-7:] == 'MTL.txt')
        self.lines = [l.lstrip().rstrip() for l in
                      open(datadir + '/' + metadata, 'r')]

        self.fields = {l.split(' = ')[0]: l.split(' = ')[-1] for l in
                       self.lines if len(l.split(' = ')) > 1}

        datafiles = [datadir + '/' + f for f in filelist if f[-3:] == 'TIF']
        bands = [l.split('_')[-1].split('.')[0] for l in datafiles]

        self.bandfiles = {b: d for b, d in zip(bands, datafiles)}

    def getBandTOARadiance(self, band):
        """ Get top of atmosphere radiance for a specific band
        """

        filename = self.bandfiles[band]
        gain = float(self.fields['RADIANCE_MULT_BAND_' + band[-1]])

        bias = float(self.fields['RADIANCE_ADD_BAND_' + band[-1]])
        datafobj = gdal.Open(filename)
        data = datafobj.GetRasterBand(1).ReadAsArray()

        return data*gain + bias

    def getBandTOAReflectance(self, band, corrected=True):

        """ Compute the Top of atmosphere reflectance for a specific band
        """

        filename = self.bandfiles[band]

        gain = float(self.fields['REFLECTANCE_MULT_BAND_' + band[-1]])
        bias = float(self.fields['REFLECTANCE_ADD_BAND_' + band[-1]])

        datafobj = gdal.Open(filename)
        data = datafobj.GetRasterBand(1).ReadAsArray()
        # data[data < .05] = np.nan

        reflectance = data*gain + bias

        if corrected is True:
            solar_elev_angle = float(self.fields['SUN_ELEVATION'])*np.pi/180

            reflectance = reflectance/np.sin(solar_elev_angle)

        return reflectance

    def getNDVI(self):

        """ Compute the NDVI
        """

        reflect_red = self.getBandTOAReflectance('B3')
        reflect_nir = self.getBandTOAReflectance('B4')

        return (reflect_nir - reflect_red)/(reflect_nir + reflect_red)

    def getEmissivity(self):

        ndvi = self.getNDVI()
        ndvimin = np.min(ndvi)
        ndvimax = np.max(ndvi)

        veg_proportion = ((ndvi - ndvimin)/(ndvimax - ndvimin))**2

        emiss = .004*veg_proportion + .986

        return emiss

    def getTOABrightnessTemp(self):

        radianceThermal = self.getBandTOARadiance('B6')
        K1 = float(self.fields['K1_CONSTANT_BAND_6'])
        K2 = float(self.fields['K2_CONSTANT_BAND_6'])

        BT = K2/(np.log(K1/radianceThermal) + 1)

        return BT

    def estimateLST(self):
        BT = self.getTOABrightnessTemp()
        emiss = self.getEmissivity()
        p = 1.438e2
        therm_wavelength = 11.45

        LST = BT/(1 + np.log(emiss)*therm_wavelength*BT/p)
        return LST
