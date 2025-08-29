import math
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()
ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("ERRO: A chave MAPBOX_ACCESS_TOKEN não foi encontrada no ficheiro .env!")
    exit()

LAT_MIN = -3.560
LAT_MAX = -3.520
LON_MIN = -38.825
LON_MAX = -38.792

ZOOM_LEVELS = range(15, 19) 

MAP_STYLE = "satellite-v9"

OUTPUT_DIR = "tiles"

TILES_EXTRA = [
    (16, 25706, 33411), (16, 25707, 33410), (16, 25706, 33409),
    (16, 25707, 33411), (16, 25707, 33409), (16, 25706, 33410),
    (16, 25701, 33409), (16, 25702, 33409), (16, 25703, 33409),
    (16, 25701, 33410), (16, 25702, 33410), (16, 25703, 33410),
    (16, 25701, 33411), (16, 25702, 33411), (16, 25703, 33411),
    (18, 102817, 133637), (18, 102818, 133637), (18, 102817, 133636),
    (18, 102818, 133636), (18, 102820, 133636), (18, 102819, 133636),
    (18, 102820, 133637), (18, 102815, 133637), (18, 102816, 133636),
    (18, 102815, 133636), (18, 102816, 133637), (18, 102819, 133637),
]


def deg_to_tile(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


if __name__ == "__main__":
    print("Iniciando o download dos tiles do mapa...")
    
    tiles_to_download_set = set()

    print("Calculando tiles da área geográfica...")
    for zoom in ZOOM_LEVELS:
        top_left = deg_to_tile(LAT_MAX, LON_MIN, zoom)
        bottom_right = deg_to_tile(LAT_MIN, LON_MAX, zoom)
        x_start, y_start = top_left
        x_end, y_end = bottom_right
        
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                tiles_to_download_set.add((zoom, x, y))

    print(f"Adicionando {len(TILES_EXTRA)} tiles específicos à lista.")
    for tile in TILES_EXTRA:
        tiles_to_download_set.add(tile)

    tiles_to_process = [t for t in tiles_to_download_set if not os.path.exists(os.path.join(OUTPUT_DIR, str(t[0]), str(t[1]), f"{t[2]}.png"))]
    total_to_download = len(tiles_to_process)

    if total_to_download == 0:
        print("Nenhum tile novo para baixar. A sua pasta 'tiles' já está completa.")
        exit()

    print(f"\nTotal de tiles a serem baixados: {total_to_download}")
    confirm = input("Deseja continuar? (s/n): ")

    if confirm.lower() != 's':
        print("Download cancelado.")
        exit()

    downloaded_count = 0
    for zoom, x, y in tiles_to_process:
        tile_url = f"https://api.mapbox.com/styles/v1/mapbox/{MAP_STYLE}/tiles/{zoom}/{x}/{y}?access_token={ACCESS_TOKEN}"
        output_path = os.path.join(OUTPUT_DIR, str(zoom), str(x), f"{y}.png")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            response = requests.get(tile_url, stream=True, timeout=10)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            downloaded_count += 1
            progress = (downloaded_count / total_to_download) * 100
            print(f"Progresso: {progress:.2f}% ({downloaded_count}/{total_to_download})", end='\r')
            
            time.sleep(0.05)

        except requests.exceptions.RequestException as e:
            print(f"\nErro ao baixar o tile {zoom}/{x}/{y}: {e}")

    print("\nDownload concluído com sucesso!")