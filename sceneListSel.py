import sys
import argparse as arg
import pandas as pd
import os
import ggStorage as gg
from datetime import datetime
import datetime
import numpy as np
from colorama import Fore, Style, init
init(convert=True)
    
# Arguments **

parser = arg.ArgumentParser()

parser.add_argument("-v", "--verbose"         , help="Show debug info", action="store_true")
parser.add_argument("-f", "--file"            , help="File with the chosen products")
parser.add_argument("-o", "--out"             , help="Output directory")
parser.add_argument("-s", "--start_date"      , help="Start date")
parser.add_argument("-e", "--end_date"        , help="End date")
parser.add_argument("-c", "--cloud"           , help="Maximum cloud cover")
parser.add_argument("-l", "--list_mgrs"       , help="Tiles corresponding to coordinates MGRS, format: -l ", type=list, nargs='*')

args = parser.parse_args()


verbose = args.verbose


if not args.file:
    print(Fore.RED + f'You have to enter the file with the catalog')
    exit(-1)
if not os.path.isfile(args.file):
    print(Fore.RED + f'Catalog file does not exist')
    exit(-1)
if not args.out:
    print(Fore.RED + f'You have to enter the output path file')
    exit(-1)
else: 
    if args.out[-3:] != 'csv':
        print(Fore.RED + 'You have to write an output csv')
        exit(-1)
print('\n\n')

if verbose:
    print('Loading the catalog into memory...  ', end="")
    
sel  = ['PRODUCT_ID', 'MGRS_TILE', 'SENSING_TIME', 'CLOUD_COVER', 'BASE_URL']
#MGRS = ['31TEE', '31TDE', '31SDD', '31SED']
ch   = 1000
df   = pd.read_csv(args.file, chunksize=ch)                    # Abrimos el catálogo en bloques de 1000 en 1000
df   = pd.concat([aux[sel] for aux in df])

if verbose:
    print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")
    
    
if args.list_mgrs:
    MGRS = [''.join(elem) for elem in args.list_mgrs]
    
    if verbose:
        print(f'Selecting tiles corresponding to MGRS coordinates {MGRS}...  ', end="")
     
    df   = df[df.MGRS_TILE.isin(MGRS)]
    
    if verbose:
        print(Fore.GREEN + 'DONE' + Fore.WHITE+ '\n', end="\n")
    
    
if args.cloud:
    if verbose:
        print(f'Selecting products with a maximum of {args.cloud}% clouds...  ', end="")
    df   = df[df.CLOUD_COVER <= float(args.cloud)]
    if verbose:
        print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")
        
df   = df.sort_values('SENSING_TIME')
df['SENSING_TIME'] = pd.to_datetime(df['SENSING_TIME'])


if verbose:
    print('Selecting dates...  ', end="")
    
if args.start_date:
    df = df[df.SENSING_TIME >=  args.start_date]

if args.end_date:
    df = df[df.SENSING_TIME <=  args.end_date]

if verbose:
    print(Fore.GREEN + 'DONE' + Fore.WHITE+ '\n', end="\n")
    
if verbose:
    print(df.reset_index()['SENSING_TIME'])
    print('\n' + 'Exporting...  ', end="")
    
df.to_csv(args.out)

if verbose:
    print(Fore.GREEN + 'DONE' + Fore.WHITE + '\n', end="\n")