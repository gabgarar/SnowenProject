import numpy as np

''' 
    calcRadianceToa
    ................................................................
    :param bandi  -> número de banda
    :param params -> parámetros MTL
    :param img    -> imagen a corregir
    
    :ret          -> imagen en radiancia TOA

'''
def calcRadianceToa(bandi, params, img):
    gain, bias = float(params[f'RADIANCE_MULT_BAND_{bandi}']), float(params[f'RADIANCE_ADD_BAND_{bandi}'])
    return gain * img + bias


''' 
    calcReflectanceToa
    ................................................................
    :param bandi  -> número de banda
    :param params -> parámetros MTL
    :param img    -> imagen a corregir
    
    :ret          -> imagen en reflectancia TOA

'''
def calcReflectanceToa(bandi, params, img):
    gain, bias = float(params[f'REFLECTANCE_MULT_BAND_{bandi}']), float(params[f'REFLECTANCE_ADD_BAND_{bandi}'])
    return (gain * img + bias) / np.sin(float(params['SUN_ELEVATION']))



''' 
    atmosCorrection
    ................................................................
    :param bandi  -> número de banda
    :param params -> parámetros MTL
    :param img    -> imagen a corregir
    :param mode   -> modo de corrección
    
    :ret          -> imagen corregida de la forma mode escogida

'''
def atmosCorrection(bandi, params, img, mode):
    
    Lmin    = float(params[f'RADIANCE_MINIMUM_BAND_{bandi}'])  
    d       = float(params['EARTH_SUN_DISTANCE'])             
    ang     = float(params['SUN_ELEVATION'])
    Lmax    = float(params[f'RADIANCE_MAXIMUM_BAND_{bandi}'])
    Rmax    = float(params[f'REFLECTANCE_MAXIMUM_BAND_{bandi}'])
    
    Esun = np.pi * (d**2) * Lmax / Rmax
    #Esun    = {2:2067, 3:1893, 4:1603, 5:972.6, 6:245.0, 7:79.72, 9:399.7}
    #Esun    = Esun[bandi]
    print(Esun)
    
    # Corrección atmosférica - Parámetros
    if mode == 'refTOA':
        return calcReflectanceToa(bandi, params, img)
    elif mode == 'radTOA':
        return calcRadianceToa(bandi, params, img)
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
    
    return num/deno
    #bruma = Lmin - (0.01 * Tz * Esun * np.sin(ang * np.pi / 180)) / (np.pi * (d**2))   
    #return np.pi * (img - bruma) / Tv * (Tz * Esun * np.sin(ang * np.pi / 180) + Edown)