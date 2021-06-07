import os
import numpy as np
from os.path import join


''' 
    bePolite
    ................................................................
    :ret          -> void

'''
def bePolite():
    print("HELLO")
    

''' 
    makeFolder
    ................................................................
    :param path -> ruta en la que generar la carpeta destino
    
    :ret        -> void

'''
def makeFolder(path):
    try:
        os.makedirs(path, exist_ok=True)
    except:
        pass
    
    
    
    
''' 
    jjoinBand
    ................................................................
    :param folder -> carpeta contenedora de todas las bandas
    :param bandi  -> seleccionar la banda i de dicha carpeta
    :param params -> parámetros MTL
    
    :ret          -> ruta de archivo a la banda i 

'''
def jjoinBand(folder, bandi, params):
    return join(folder, params[f'FILE_NAME_BAND_{bandi}'].split('"')[1])


''' 
    parseBands
    ................................................................
    :param folder -> carpeta contenedora de todas las bandas
    :param params -> parámetros MTL
    :param lst    -> lista de bandas i de la que se quiere obtener su ruta de archivo
    
    :ret          -> lista de rutas de acceso a las bandas i 

'''
def parseBands(folder, params, lst):
    if params['SPACECRAFT_ID'] == '"LANDSAT_8"':
        return [jjoinBand(folder, bandi, params) for bandi in lst]
    else:
        raise Exception('ERROR: Satélite desconocido')
        

''' 
    calcNormIndex
    ................................................................
    :param imgs -> imágenes sobre los que hacer el índice normalizado
    
    :ret        -> índice normalizado

'''
def calcNormIndex(imgs):
    np.seterr(invalid='ignore')
    return (imgs[1] - imgs[0]) / (imgs[1] + imgs[0])


''' 
    norm
    ................................................................
    :param img -> imagen 
    
    :ret       -> imagen cuyos valores son normalizados entre 0 y 1

'''
def norm(img):
    return (img - np.min(img)) / (np.max(img) - np.min(img))