'''                                                            
                                                                                                            ,,                           
 .M"""bgd                                                                                                   db                     mm    
,MI    "Y                                                                                                                          MM    
`MMb.     `7MMpMMMb.   ,pW"Wq.  `7M'    ,A    `MF' .gP"Ya  `7MMpMMMb.      `7MMpdMAo. `7Mb,od8  ,pW"Wq.   `7MM  .gP"Ya   ,p6"bo  mmMMmm  
  `YMMNq.   MM    MM  6W'   `Wb   VA   ,VAA   ,V  ,M'   Yb   MM    MM        MM   `Wb   MM' "' 6W'   `Wb    MM ,M'   Yb 6M'  OO    MM    
.     `MM   MM    MM  8M     M8    VA ,V  VA ,V   8M""""""   MM    MM        MM    M8   MM     8M     M8    MM 8M"""""" 8M         MM    
Mb     dM   MM    MM  YA.   ,A9     VVV    VVV    YM.    ,   MM    MM        MM   ,AP   MM     YA.   ,A9    MM YM.    , YM.    ,   MM    
P"Ybmmd"  .JMML  JMML. `Ybmd9'       W      W      `Mbmmd' .JMML  JMML.      MMbmmd'  .JMML.    `Ybmd9'     MM  `Mbmmd'  YMbmd'    `Mbmo 
                                                                             MM                          QO MP                           
                                                                           .JMML.                        `bmP                            


By Gabriel García García


                                                            
'''
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

                                                          LIBRARIES
        
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
import os
from os.path import dirname, realpath, join

import glob
from osgeo import gdal, gdalconst, osr

import folium
from folium.raster_layers import ImageOverlay
from folium.plugins import MeasureControl
from folium import plugins

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage
from skimage import measure
from shapely.geometry import mapping, Polygon, Point
import fiona
from fiona.crs import from_epsg

import geopandas as gpd
import pandas as pd

import ogr
import subprocess
from branca.element import Template, MacroElement
from math import radians, sin


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

                                                          GENERALS   
        
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

## SAY HELLO ##

def bePolite():
    print("HELLO")
    
    
def makeFolder(path):
    try:
        os.makedirs(path, exist_ok=True)
    except:
        pass



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

                                                       STACK OPERATIONS
        
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def stack(pt, tifs):
    return gdal.Translate(pt, gdal.BuildVRT('/vsimem/stacked.vrt', tifs, separate=True))

def stackBands(folder):
    tifs = glob.glob(join(folder, '*.tif'))
    print(tifs)
    #tifs.sort(key=len)
    print("stack", join(folder,'stack.tif'))
    stack(join(folder,'stack.tif'), tifs)
    
def loadRasterStack(bandPath, bands): #bands in [2, 3, 4...]
    raster_ds = gdal.Open(bandPath, gdal.GA_ReadOnly)
    if raster_ds is None:
        raise Exception("can't open stack file")
    return raster_ds, [raster_ds.GetRasterBand(elem).ReadAsArray() for elem in bands] # raster object and images in those bands




'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

                                                     SINGLE BAND OPERATION
        
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# Leer una imagen individual
def loadRasterImage(path):
    raster_ds = gdal.Open(path, gdal.GA_ReadOnly)
    if raster_ds is None:
        raise Exception("No se puede abrir el archivo tif")
    return raster_ds, raster_ds.GetRasterBand(1).ReadAsArray()#.astype(np.float32)
    
def saveBandAsTiff(dst, rt, img, tt):
    transform = rt.GetGeoTransform()
    geotiff = gdal.GetDriverByName('GTiff')
    output = geotiff.Create(dst, rt.RasterXSize, rt.RasterYSize, 1,tt)
    wkt = rt.GetProjection()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)
    output.GetRasterBand(1).WriteArray(np.array(img))
    output.GetRasterBand(1).SetNoDataValue(-999)
    output.SetGeoTransform(transform)
    output.SetProjection(srs.ExportToWkt())
    output = None
    
    
    
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

                                                     INDEX OPERATIONS
        
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def calcNormIndex(imgs):
    np.seterr(invalid='ignore')
    return (imgs[1] - imgs[0]) / (imgs[1] + imgs[0])

def norm(img):
    return (img - np.min(img)) / (np.max(img) - np.min(img))

   
# Generar máscara de agua
def genMaskAgua(img, perc):
    return (np.iinfo(img.dtype).max - img) >= (np.iinfo(img.dtype).max * perc)



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

                                                    SHAPEFILES OPERATIONS 
        
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# Merge shapefiles
def mergeShapes(path):
    cont = gpd.GeoDataFrame(columns=['id', 'date', 'geometry', 'surface', 'threshold'])
    for file in glob.glob(join(path, '**/*.shp')):
        df = gpd.read_file(file)
        df['threshold'] = file.split('_')[-2]
        cont = cont.append(df)
    cont = cont.to_crs("EPSG:4326")
    cont.to_file(join(path, 'Snowen.shp'), driver='ESRI Shapefile', crs=from_epsg(4326))

# Obtención de contornos (sobre máscara)
def getContoursMask(imgData):
    kernel = np.asarray([[1, 2, 1], [2, 2, 2], [1, 2, 1]])
    api = ndimage.convolve(imgData.copy(), kernel)
    return measure.find_contours(api, 1, fully_connected='low',positive_orientation='high')


# Pasar los píxeles de una capa a coordenadas xy
def pix2xyGDAL(row, col, affine):
    xoff, a, b, yoff, d, e = affine
    return float(col * a + row * b + xoff), float(col * d + row * e + yoff)
    

# Listado de polígonos, transformados de píxeles a coordenadas x, y
def getPolygons(contours, affine, marg):
    return [Polygon([pix2xyGDAL(x, y, affine) for x, y in elem]) 
             for elem in contours if np.shape(elem)[0] > marg
            ]

# Reestructurar la geometria

def generateHerarchy(geometry):
    pols, holes = [], []
    for posi, grande in enumerate(geometry):
        ret = []
        for posj, p in enumerate(geometry):
            if ( posj != posi and p.within(grande)):
                ret.append(p)
                holes.append(p)
        if grande not in holes:
            aux = Polygon(grande.exterior.coords, [r.exterior.coords for r in ret]) if len(ret) > 0 else Polygon(grande.exterior.coords)
            pols.append(aux)
    return pols


        
    
def createShapeFileContoursGDAL(contours, rt,  crs, dst, date, mrs=10):
    print(f'MRS: {mrs}')
    sc = {'geometry': 'Polygon','properties': {'id': 'int', 'date': 'str', 'area':'float'}}
    
    polis = getPolygons(contours, rt.GetGeoTransform(), mrs)
    print("hh:: La lista tiene un total de : ", len(polis))
    polis = generateHerarchy(polis)
    print("CRS", from_epsg(crs))
    with fiona.open(dst, 'w', 'ESRI Shapefile',crs=from_epsg(crs), schema=sc) as c:  # creates new file to be written to
        {c.write({'geometry': mapping(polis[j]),'properties': {'id': j, 'date': date, 'area': polis[j].area},}) for j in range(len(polis))}


def generateShapes(img, rt, threshold, ops): 

    # Generamos las capas referentes
    SCAconts = getContoursMask(img)

    # Sacamos informacion del sistema de referencia
    proj = osr.SpatialReference(wkt=rt.GetProjection())

    # Almacenamos los contornos en un archivo shp
    dst_shp = join(ops['PathShapes'], ops['date'].replace(':','_'))
    makeFolder(dst_shp)
    dst_shp = join(dst_shp, f'sn_{int(threshold*10)}_.shp')
    createShapeFileContoursGDAL(SCAconts, rt, proj.GetAttrValue('AUTHORITY',1), dst_shp, ops['date'], ops['mrs'])


      
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

                                                    REFLECTANCE 
        
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def readMTL(path):
    ret = {}
    with open(path, 'r') as f:
        for linea in f:
            aux = linea.split()
            ret[aux[0]] = aux[2] if len(aux) > 1 else None
    return ret

def calcRadianceToa(bandi, params, img):
    gain, bias = float(params[f'RADIANCE_MULT_BAND_{bandi}']), float(params[f'RADIANCE_ADD_BAND_{bandi}'])
    return gain * img + bias

def calcReflectanceToa(bandi, params, img):
    gain, bias = float(params[f'REFLECTANCE_MULT_BAND_{bandi}']), float(params[f'REFLECTANCE_ADD_BAND_{bandi}'])
    return (gain * img + bias) / np.sin(float(params['SUN_ELEVATION']))

def atmosCorrection(bandi, params, img, mode):
    
    Lmin    = float(params[f'RADIANCE_MINIMUM_BAND_{bandi}'])  
    d       = float(params['EARTH_SUN_DISTANCE'])             
    ang     = float(params['SUN_ELEVATION'])
    Lmax    = float(params[f'RADIANCE_MAXIMUM_BAND_{bandi}'])
    Rmax    = float(params[f'REFLECTANCE_MAXIMUM_BAND_{bandi}'])
    Esun    = np.pi * (d**2) * Lmax / Rmax
                 
    
    # Corrección atmosférica - Parámetros
    if mode == 'TOA':
        return calcReflectanceToa(bandi, params, img)
    elif mode == 'DOS1':
        Edown, Tv, Tz = 0, 1, 1
    elif mode == 'DOS2':  
        Edown, Tv = 0, 1 
        Tz = np.sin(ang * np.pi / 180) if bandi <= 5 else 1   # Para Landsat 8
    
        
    # Tranformación de valores digitales a radiancia TOA (Caso Landsat)
    img     = calcRadianceToa(bandi, params, img)  
    
    # Correccióm atmosférica - Ecuación DOS
    bruma = Lmin - (0.01 * Tv * (Esun * Tz * np.sin(ang * np.pi / 180) + Edown))/(np.pi * (d**2))
    num   = np.pi * (d**2) * (img - bruma)
    deno  = Tv * (Tz * Esun * np.sin(ang * np.pi / 180) + Edown)
    return num / deno


        
