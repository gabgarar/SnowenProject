import fiona
import Utils as ut
import numpy as np
import geopandas as gpd
from scipy import ndimage
from skimage import measure
from fiona.crs import from_epsg
from osgeo import gdal, gdalconst, osr
from os.path import dirname, realpath, join
from shapely.geometry import mapping, Polygon, Point



''' 
    getContoursMask
    ................................................................
    :param img    -> imagen de la que se quiere sacar los contornos
    
    :ret          -> contornos de la imagen

'''
def getContoursMask(img):
    kernel = np.asarray([[1, 2, 1], [2, 2, 2], [1, 2, 1]])
    api = ndimage.convolve(img.copy(), kernel)
    return measure.find_contours(api, 1, fully_connected='low',positive_orientation='low')

''' 
    pix2xy
    ................................................................
    :param row    -> posición x del píxel
    :param col    -> posición y del píxel
    :param affine -> variables asociadas al paso de posición píxel a posición en coordenadas xy
    
    :ret          -> posición xy píxel a coordenada xy

'''
def pix2xy(row, col, affine):
    xoff, a, b, yoff, d, e = affine
    return float(col * a + row * b + xoff ), float(col * d + row * e + yoff)


''' 
    getPolygons
    ................................................................
    :param contours -> lista de contornos de la imagen
    :param affine   -> variables asociadas al paso de posición píxel a posición en coordenadas xy
    :param ops      -> parametro configuracion json usuario 
    
    :ret            -> lista de polígonos dada una lista de contornos

'''
def getPolygons(contours, affine, ops):
    mrs = ops['mrs']
    colAdd, rowAdd , *_ = ops['aoi']
    return [Polygon([pix2xy(x + rowAdd, y + colAdd, affine) for x, y in elem]) 
             for elem in contours if np.shape(elem)[0] > mrs
            ]


''' 
    generateHerarchy
    ................................................................
    :param geometry -> dada una lista de polígonos, genera una jerarquía de polígonos con agujeros
    
    :ret            -> lista de polígonos con jerarquía de agujeros

'''
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


''' 
    createShapeFileContoursGDAL
    ................................................................
    :param contours -> lista de contornos de la imagen
    :param rt       -> cabecera de metadatos imagen
    :param dst      -> ruta destino a almacenar el fichero
    :param ops      -> parametro configuracion json usuario
    
    :ret            -> void

'''
def createShapeFileContoursGDAL(contours, rt, dst, ops):
    
    # Información del sistema de referencia
    proj  = osr.SpatialReference(wkt=rt.GetProjection())
    crs   = proj.GetAttrValue('AUTHORITY',1)
    
    polis = getPolygons(contours, rt.GetGeoTransform(), ops)
    print("Hay un total de ", len(polis), 'polígonos.')
    print("Generando jerarquía ... ")
    polis = generateHerarchy(polis)
    print("Almacenando ... ")
    sc = {'geometry': 'Polygon','properties': {'id': 'int', 'date': 'str', 'area':'float'}}
    with fiona.open(dst, 'w', 'ESRI Shapefile',crs=from_epsg(crs), schema=sc) as c:  # creates new file to be written to
        {c.write({'geometry': mapping(polis[j]),'properties': {'id': j, 'date': ops['date'], 'area': polis[j].area},}) for j in range(len(polis))}
        
        
''' 
    generateShapes
    ................................................................
    :param img -> imagen a vectorizar
    :param rt  -> cabecera de metadatos imagen
    :param ops -> parámetros configuracion json usuario
    
    :ret       -> void

'''
def generateShapes(img, rt, ops): 

    # Generamos las capas referentes
    SCAconts = getContoursMask(img)


    # Archivo shp destino identificada con la fecha
    dst_shp = join(ops['out'], ops['PathShapes'], ops['date'].replace(':','_'))
    
    # Creamos la carpeta de salida
    ut.makeFolder(dst_shp)
    
    dst_shp = join(dst_shp, f'sn_presencia.shp')
    createShapeFileContoursGDAL(SCAconts, rt, dst_shp, ops)
    
    

# Merge shapefiles
def mergeShapes(path):
    cont = gpd.GeoDataFrame(columns=['id', 'date', 'geometry', 'surface', 'threshold'])
    for file in glob.glob(join(path, '**/*.shp')):
        df = gpd.read_file(file)
        df['threshold'] = file.split('_')[-2]
        cont = cont.append(df)
    cont = cont.to_crs("EPSG:4326")
    cont.to_file(join(path, 'Snowen.shp'), driver='ESRI Shapefile', crs=from_epsg(4326))