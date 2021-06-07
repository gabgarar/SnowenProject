
from osgeo import gdal, gdalconst, osr
import numpy as np
import pandas as pd


''' 
    readOnMTL
    ................................................................
    :param ulr -> indica la ulr al archivo MTL
    
    :ret       -> dictado de parámetros MTL

'''
def readOnMTL(url):
    MTL, ret = pd.read_fwf( url ,header=None).values.tolist(), {}
    for linea in MTL:
        aux = linea[0].split()
        ret[aux[0]] = aux[2] if len(aux) > 1 else None
    return ret


''' 
    readMTL
    ................................................................
    :param path    -> indica la ruta del archivo de metadatos MTL
    
    :ret           -> dictado de parámetros MTL

'''
def readMTL(path):
    ret = {}
    with open(path, 'r') as f:
        for linea in f:
            aux = linea.split()
            ret[aux[0]] = aux[2] if len(aux) > 1 else None
    return ret


''' 
    loadRasterImage
    ................................................................
    :param path    -> indica la ruta de la que leer los datos
    :param limits  -> zona AOI de la imagen a leer de los datos
    
    :ret           -> cabecera con metadatos e imagen

'''
def loadRasterImage(path, limits=None):
    raster_ds = gdal.Open(path, gdal.GA_ReadOnly)
    if raster_ds is None:
        raise Exception("No se puede abrir el archivo tif")
    if limits is not None:
        xoff, yoff, xcount, ycount = limits # limits as (a, b, c, d)
        im = raster_ds.GetRasterBand(1).ReadAsArray(xoff, yoff, xcount, ycount)
    else:
        im = raster_ds.GetRasterBand(1).ReadAsArray()
    
    return raster_ds, im
    
    
''' 
    saveBandAsTiff
    ................................................................
    :param dst  -> ruta de destino del archivo
    :param rt   -> cabecera de metadatos del archivo
    :param img  -> imagen a almacenar
    :param tt   -> tipo de almacenamiento de los datos en el fichero
    :param typ  -> tipo de fichero
    
    :ret       -> cabecera con metadatos e imagen

'''
def saveBandAsTiff(dst, rt, img, tt=gdal.GDT_Float64):
    transform = rt.GetGeoTransform()
    geotiff = gdal.GetDriverByName(str('GTiff'))
    output = geotiff.Create(dst, rt.RasterXSize, rt.RasterYSize, 1,tt)
    #output = geotiff.Create(dst, img.shape[1], img.shape[0], 1, tt)
    wkt = rt.GetProjection()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)
    output.GetRasterBand(1).WriteArray(np.array(img))
    output.GetRasterBand(1).SetNoDataValue(-999)
    output.SetGeoTransform(transform)
    output.SetProjection(srs.ExportToWkt())
    output = None
    
    
    

''' 
    stack
    ................................................................
    :param inp -> lista de imágenes a juntar en un stack (img1, img2...)
    
    :ret       -> matriz multidimensional con n bandas de ancho en funcion del número de entradas
'''    
def stack(*inp):
    w, h = inp[0].shape
    stack = np.zeros([w, h, len(inp)])
    for i in range(len(inp)):
        stack[:, :, i] = inp[i]
    return stack