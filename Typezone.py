from flask import Flask, request, jsonify  
import geopandas as gpd  
from shapely.geometry import Point 
import numpy as np 
import os
import gdown 
import math  # Pour vérifier les NaN

app = Flask(__name__)  

# ==========================
# CONFIGURATION
# ==========================

GPKG_PATH = "Typezone.gpkg"
GPKG_LAYER = "vectoris"
GPKG_FILE_ID = "14j0-YSGq7MFCLHUtTaQ0Rs3pWvCSU0lZ"  # 🔁 Remplace ceci par ton vrai ID Google Drive

# ==========================
# TÉLÉCHARGEMENT SI NÉCESSAIRE
# ==========================

def download_file(file_id, dest_path):
    url = f"https://drive.google.com/uc?id={file_id}"
    if not os.path.exists(dest_path):
        print(f"📥 Téléchargement de {dest_path} depuis Google Drive...")
        gdown.download(url, dest_path, quiet=False)
    else:
        print(f"✅ {dest_path} déjà présent.")

download_file(GPKG_FILE_ID, GPKG_PATH)

# ==========================
# CHARGEMENT DU GPKG
# ==========================

zones_gdf = gpd.read_file(GPKG_PATH, layer=GPKG_LAYER)
zones_gdf = zones_gdf.to_crs(epsg=4326)

# ==========================
# ROUTE API
# ==========================

@app.route('/zone-type', methods=['POST'])
def get_zone_type():
    data = request.get_json()
    results = []

    for point_data in data['points']:
        lon = point_data['longitude']
        lat = point_data['latitude']

        point = gpd.GeoDataFrame(
            geometry=[Point(lon, lat)],
            crs="EPSG:4326"  
        )

        # Jointure spatiale
        match = gpd.sjoin(point, zones_gdf, how="left", predicate="intersects")
        
        # Récupération du type de zone
        if not match.empty:
            zone = match.iloc[0]
            zone_type = zone['Type_zone']

            # Gestion des cas NaN/None → 50
            if zone_type is None or (isinstance(zone_type, float) and math.isnan(zone_type)):
                zone_type = 50
            elif isinstance(zone_type, (np.integer, np.int32, np.int64)):
                zone_type = int(zone_type)
        else:
            zone_type = 50  # Aucune zone trouvée → 50 par défaut

        results.append({
            "longitude": lon,
            "latitude": lat,
            "zone_type": zone_type
        })

    return jsonify(results)

# ==========================
# LANCEMENT
# ==========================

if __name__ == '__main__':
    app.run(port=5001, debug=True)
