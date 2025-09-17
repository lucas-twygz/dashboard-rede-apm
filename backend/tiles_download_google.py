import math
import os
import requests
import time
import sys
import random

# --- CONFIGURAÇÃO ---
# Área expandida para garantir a cobertura de todas as áreas (Pátio, TMUT, Depot)
LAT_MIN = -3.595
LAT_MAX = -3.520
LON_MIN = -38.850
LON_MAX = -38.790

ZOOM_LEVELS = range(13, 17) 

# Caminho de saída final. Execute o script da raiz do projeto.
OUTPUT_DIR = os.path.join("static", "tiles")

# Lista completa com todos os tiles que já foram reportados como faltando
TILES_EXTRA = [
    (17, 51405, 66829), (17, 51404, 66829), (17, 51405, 66828), (17, 51404, 66828),
    (17, 51405, 66830), (17, 51404, 66830), (17, 51406, 66829), (17, 51403, 66829),
    (17, 51406, 66828), (17, 51403, 66828), (17, 51405, 66827), (17, 51404, 66827),
    (17, 51406, 66830), (17, 51405, 66831), (17, 51404, 66831), (17, 51403, 66827),
    (17, 51407, 66829), (17, 51402, 66828), (17, 51406, 66831), (17, 51407, 66830),
    (17, 51404, 66826), (17, 51402, 66827), (16, 25702, 33414), (16, 25702, 33415),
    (16, 25703, 33414), (16, 25701, 33414), (16, 25702, 33413), (16, 25703, 33415),
    (16, 25701, 33413), (15, 12851, 16707), (15, 12850, 16707), (15, 12851, 16706),
    (15, 12850, 16706), (14, 6425, 8353), (13, 3212, 4176), (12, 1606, 2088),
    (11, 803, 1044), (10, 401, 522), (9, 200, 261), (8, 100, 130), (7, 50, 65),
    (17, 51410, 66820), (17, 51409, 66820), (17, 51410, 66819), (17, 51410, 66821),
    (17, 51409, 66819), (17, 51409, 66821), (17, 51411, 66820), (17, 51411, 66819),
    (17, 51408, 66820), (17, 51411, 66821), (17, 51408, 66819), (17, 51410, 66818),
    (17, 51408, 66821), (17, 51409, 66818), (17, 51410, 66822), (17, 51409, 66822),
    (17, 51412, 66820), (17, 51411, 66818), (17, 51411, 66822), (17, 51412, 66819),
    (17, 51408, 66818), (17, 51412, 66821), (17, 51407, 66820), (17, 51407, 66819),
    (17, 51410, 66817), (17, 51409, 66817), (17, 51410, 66823), (17, 51412, 66822),
    (17, 51407, 66818), (17, 51411, 66823), (17, 51408, 66817), (17, 51413, 66821),
    (17, 51406, 66819), (17, 51412, 66823), (17, 51413, 66822), (17, 51407, 66817),
    (17, 51409, 66816), (17, 51406, 66818), (17, 51411, 66824), (16, 25705, 33410),
    (16, 25704, 33410), (16, 25705, 33409), (16, 25704, 33409), (16, 25705, 33411),
    (16, 25704, 33411), (16, 25705, 33408), (16, 25704, 33408), (16, 25703, 33408),
    (16, 25705, 33412), (15, 12852, 16705), (15, 12852, 16704), (15, 12851, 16704),
    (15, 12852, 16706), (14, 6426, 8352), (14, 6425, 8352), (14, 6426, 8353),
    (13, 3213, 4176), (16, 25706, 33410), (16, 25706, 33409), (16, 25706, 33411)
]

def deg_to_tile(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

if __name__ == "__main__":
    print("Iniciando o download dos tiles de satélite do Google Maps (Versão Final)...")
    
    tiles_to_download_set = set(TILES_EXTRA)

    print("Calculando tiles para a área geográfica expandida...")
    for zoom in ZOOM_LEVELS:
        top_left = deg_to_tile(LAT_MAX, LON_MIN, zoom)
        bottom_right = deg_to_tile(LAT_MIN, LON_MAX, zoom)
        x_start, y_start = top_left
        x_end, y_end = bottom_right
        
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                tiles_to_download_set.add((zoom, x, y))

    tiles_to_process = sorted([t for t in tiles_to_download_set if not os.path.exists(os.path.join(OUTPUT_DIR, str(t[0]), str(t[1]), f"{t[2]}.png"))])
    total_to_download = len(tiles_to_process)

    if total_to_download == 0:
        print("\nNenhum tile novo para baixar. A sua pasta 'tiles' já está completa.")
        exit()

    print(f"\nTotal de tiles novos a serem baixados: {total_to_download}")
    confirm = input("Deseja continuar? (s/n): ")

    if confirm.lower() != 's':
        print("Download cancelado.")
        exit()

    downloaded_count = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print("\nBaixando...")
    print_progress_bar(0, total_to_download, prefix='Progresso:', suffix='Completo', length=50)
    for i, (zoom, x, y) in enumerate(tiles_to_process):
        tile_url = f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={zoom}"
        output_path = os.path.join(OUTPUT_DIR, str(zoom), str(x), f"{y}.png")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            response = requests.get(tile_url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            time.sleep(random.uniform(0.01, 0.05))

        except requests.exceptions.RequestException as e:
            print(f"\nErro ao baixar o tile {zoom}/{x}/{y}: {e}")
        
        print_progress_bar(i + 1, total_to_download, prefix='Progresso:', suffix='Completo', length=50)

    print("\n\nDownload concluído com sucesso!")