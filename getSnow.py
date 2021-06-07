import sys
import argparse as arg
import pandas as pd
import os
from datetime import datetime
import datetime
import numpy as np
from colorama import Fore, Style, init
from osgeo import gdal
import glob
import json
import Utils as ut
import VectorRast as vr
import IoRast   as rose
from os.path import join
import TempSurface as tm
import AtmosCorrection as ac
import pandas as pd
import time

init(convert=True)


parser = arg.ArgumentParser()

# General
parser.add_argument("-v", "--verbose"         , help="Show debug info", action="store_true")
parser.add_argument("-i", "--input"           , help="Catalog file")
parser.add_argument("-o", "--out"             , help="Processing output directory")
parser.add_argument("-json", "--json"         , help="Parameter file")

# Specific
parser.add_argument("-s", "--start_date"      , help="Start date")
parser.add_argument("-e", "--end_date"        , help="End date")
parser.add_argument("-c", "--cloud"           , help="Maximum cloud cover")
parser.add_argument("-p", "--path"            , help="Path tile ")
parser.add_argument("-r", "--row"             , help="Maximum cloud cover")

args = parser.parse_args()

verbose = args.verbose



# Check the input parameter
if not args.input:
    print(Fore.RED + f'You have to enter the catalog url or file')
    exit(-1)
 
# If the output directory does not exist, it is created
if args.out:
    if not os.path.isdir(args.out):
        os.makedirs(args.out) 
else:
    print(Fore.RED + f'you have to give an output directory')
    exit(-1)
    
if verbose: 
    print("Loading catalog in memory...  ", end="\t")
    
# Read the catalog using chunks
ch   = 1000
s3_scenes = pd.read_csv(args.input, compression='gzip', chunksize=ch)
s3_scenes = pd.concat(s3_scenes)




if verbose:
    print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")
    
# Select L1TP

if verbose:
    print("Selecting L1TP Products...  ", end="\t")
    
s3_scenes = s3_scenes[(~s3_scenes.productId.str.contains('_T2')) & (~s3_scenes.productId.str.contains('_RT'))]



if verbose:
    print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")
    
# Select PATH & ROW

if args.path: 
    if verbose:
        print(f"Selecting PATH {args.path}...  ", end="\t")
        
    s3_scenes = s3_scenes[s3_scenes.path == float(args.path)] 
    
    if verbose:
        print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")
        
if args.row:
    if verbose:
        print(f"Selecting ROW {args.row}...  ", end="\t")
        
    s3_scenes = s3_scenes[s3_scenes.row == float(args.row)] 
    
    if verbose:
        print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")
    
if args.cloud:
    if verbose:
            print(f'Selecting products with a maximum of {args.cloud}% clouds...  ', end="\t")
            
    s3_scenes = s3_scenes[s3_scenes.cloudCover < float(args.cloud)]
    
    if verbose:
        print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")
    
s3_scenes = s3_scenes.sort_values('cloudCover').groupby(s3_scenes.productId).first().sort_values('acquisitionDate')

if args.start_date:
    if verbose:
        print(f'Selecting start date {args.start_date}...  ', end="\t")
        
    s3_scenes = s3_scenes[s3_scenes.acquisitionDate >=  str(args.start_date)]
    
    if verbose:
        print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")

if args.end_date:
    
    if verbose:
        print(f'Selecting end date {args.end_date}...  ', end="\t")
        
    s3_scenes = s3_scenes[s3_scenes.acquisitionDate <=  str(args.end_date)]
    
    if verbose:
        print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")


print(".-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-")


gdal.SetConfigOption('CPL_VSIL_CURL_ALLOWED_EXTENSIONS', 'tif')
gdal.SetConfigOption('VSI_CACHE', 'TRUE')
gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'TRUE')
gdal.SetConfigOption('CPL_VSIL_CURL_CHUNK_SIZE', '32768')
gdal.SetConfigOption('CPL_VSIL_CURL_CACHE_SIZE', '655360')
gdal.SetConfigOption('CPL_DEBUG', 'OFF')
gdal.SetConfigOption('AWS_NO_SIGN_REQUEST', 'YES')

# Json Parameters

with open ('config.json', 'r') as file: config = json.load(file)
config['aoi'] = None if config['aoi'] == 'None' else config['aoi']
i             = config['start_i']
config['out'] = args.out


print(config)



while i < len(s3_scenes):

    if int(str(s3_scenes.iloc[i].acquisitionDate).split('-')[1]) in config['months']: # Select the month
            
        
        if verbose: 
            print(f"Processing file:     {i}")
            print(f"Acquisition date:    {s3_scenes.iloc[i]['acquisitionDate']}")
            print(f"Cloud cover:         {s3_scenes.iloc[i]['cloudCover']}%" )
        
        # Creamos las url para cada banda vsicurl
        url = '/'.join(s3_scenes.iloc[i]['download_url'].split('/')[0:-1])
        blue, green, red, nir, swir1, tir1 = [f'/vsicurl/{url}/{s3_scenes.iloc[i].productId}_B{j}.TIF' for j in [2, 3, 4, 5, 6, 10]]

        # Creamos la url para el archivo MTL
        MTL = f'{url}/{s3_scenes.iloc[i].productId}_MTL.txt'
        
        # Cargamos contenido del archivo MTL en memoria
        params = rose.readOnMTL(MTL)
        
        # Introducimos nuevos parametros que se quitarán posteriormente
        config['date'] = params['DATE_ACQUIRED']
        #(2000, 3000, 4000, 2000) #(3000, 2000, 2000, 1000) COROPUNA

        # Cargamos las imágenes en memoria
        r1, tir1   = rose.loadRasterImage(tir1 , config['aoi'])
        r2, blue   = rose.loadRasterImage(blue , config['aoi'])
        r3, green  = rose.loadRasterImage(green, config['aoi'])
        r4, red    = rose.loadRasterImage(red  , config['aoi'])
        r5, nir    = rose.loadRasterImage(nir  , config['aoi'])
        r6, swir1  = rose.loadRasterImage(swir1, config['aoi'])
      
        if config['aoi'] is None:
            config['aoi'] = (0, 0, 0, 0)
 
        # Corregimos atmosfericamente
        blue       = ac.atmosCorrection(2, params, blue , config['mode'])
        green      = ac.atmosCorrection(3, params, green, config['mode'])
        swir1      = ac.atmosCorrection(6, params, swir1, config['mode'])


        # Generamos NDSI para calcular mascara de nieve
        NDSI       = ut.calcNormIndex([swir1, green])

        # Conseguimos la temperatura en superficie y la pasamos a grados celsius
        res        = tm.tir2Temp(red, nir, tir1, params)
        res        = res - 273.15

        # Definimos que existe presencia de nieve cuando el NDSI > 0.1 y la temperatura es mayor a -20 grados
        presencia  = (NDSI >= 0.20) & (res > -20) #-20

        # Como el NDSI tambien coge masas de agua, una forma fácil de eliminarlas es tomando como máscara, aquellas zona de temperaturas mayores a 5 grados.
        presencia &= (res < 5)

        # A su vez, se tendrá en cuenta una máscara para eliminar nubes más densas o de mayor altura, haciendo uso de la banda swir del instrumento
        presencia &= (ut.norm(blue) < 0.8) & (ut.norm(swir1) < 0.2)

        # Tras ello, añadimos las coberturas claras de nieve a la solucion
        presencia |= (NDSI >= 0.4)

        NDSI[~presencia] = config['mini']

        if config['saveTIF']:
            print('Saving snow cover raster...')
            rose.saveBandAsTiff(join(args.out,s3_scenes.iloc[i]['productId'] + '.tif' ), r6, NDSI)
        
        if config['saveSHP']:
            if verbose: 
                print('Vectorizing...')
            vr.generateShapes(NDSI, r6, config)
      
    i += 1
            
