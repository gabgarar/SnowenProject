import json
import glob
import gdal
import Snow as sn
import numpy as np
from os.path import join
from skimage import img_as_float

''' 
    radianceTOA
    ................................................................
    :param band -> indica el número de banda a usar
    :param img  -> imagen de entrada en valores digitales
    
    :ret        -> imagen en radiancia TOA

'''
def radianceTOA(band, img, params):
    # Convertimos en radiancia TOA
    Ml  = float(params[f'RADIANCE_MULT_BAND_{band}'])
    Al  = float(params[f'RADIANCE_ADD_BAND_{band}'])
    return Ml * img + Al


    
''' 
    brightTemp
    ................................................................
    :param band   -> indica el número de banda a usar
    :param img    -> imagen de entrada en valores digitales
    :param params -> datos MTL
    
    :ret          -> imagen de temperatura de brillo

'''
def brightTemp(band, img, params):

    # Convertimos a radiancia TOA
    img = radianceTOA(band, img, params)
    
    # Calculamos temperatura de brillo
    k1 = float(params[f'K1_CONSTANT_BAND_{band}'])
    k2 = float(params[f'K2_CONSTANT_BAND_{band}'])
    
    return k2 / np.log((k1 / img) + 1)
    
# PASAR DE TEMPERATURA DE BRILLO A TEMPERATURA EN SUPERFICIE

''' 
    surfaceTemp
    ................................................................
    :param img -> banda
    :param e   -> emisividad
    
    :ret       -> imagen de temperatura en superficie

'''
def surfaceTemp(img, e):
    return img / ((0.00115 * img / 1.4388) * np.log(e) + 1)


''' 
    tir2Temp
    ................................................................
    :param red    -> banda roja en crudo
    :param nir    -> banda nir en crudo
    :param tir    -> banda tir1 en crudo
    :param params -> parámetros MTL
    
    ** Engloba surfaceTemp,  brightTemp,  radianceTOA
    :ret          -> imagen de temperatura en superficie

'''
def tir2Temp(red, nir, tir1, params): # En crudo
    
    # bandas red, nir a reflectancias TOA
    red  = sn.atmosCorrection(4, params, red, 'TOA')
    nir  = sn.atmosCorrection(5, params, nir, 'TOA')

    # Calculamos el NDVI
    NDVI = sn.norm((nir - red) / (nir + red))

    # Calculamos el índice de proporción de vegetación
    PV = NDVI ** 2

    # Calculamos la emisividad
    e = 0.004 * PV + 0.986 

    # Calculamos la temperatura de brillo
    tir1 = brightTemp(10, tir1, params)

    # Calculamos la temperatura en superficie
    return surfaceTemp(tir1, e)