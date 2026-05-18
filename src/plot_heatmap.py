import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
from matplotlib.colors import LogNorm

# Konfiguracja ścieżek
FILES = {
    'Mały': 'benchmark_results_maly.json',
    'Średni': 'benchmark_results_sredni.json',
    'Duży': 'benchmark_results_duzy.json'
}

DATABASES = ['postgres', 'mysql', 'redis', 'mongodb']

def load_data():
    data = {}
    for size, file_path in FILES.items():
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data[size] = json.load(f)
        else:
            print(f"Ostrzeżenie: Plik {file_path} nie został znaleziony.")
    return data

def prepare_dataframe(data, mode):
    # mode to 'without_indexes' lub 'with_indexes'
    records = []
    for size, json_data in data.items():
        if mode not in json_data:
            continue
        
        operations = json_data[mode]
        for op_name, db_results in operations.items():
            for db in DATABASES:
                val = db_results.get(db)
                if val is not None:
                    records.append({
                        'Size': size,
                        'Operation': op_name,
                        'Database': db,
                        'Time': val
                    })
    
    if not records:
        return None
    return pd.DataFrame(records)

def plot_heatmaps(data):
    # Generujemy dwie osobne heatmapy: bez indeksów oraz z indeksami
    for mode in ['without_indexes', 'with_indexes']:
        df = prepare_dataframe(data, mode)
        if df is None:
            continue
            
        sizes = ['Mały', 'Średni', 'Duży']
        available_sizes = [s for s in sizes if s in df['Size'].unique()]
        
        if not available_sizes:
            continue
            
        # Utworzenie układu subplotów w jednym rzędzie
        fig, axes = plt.subplots(1, len(available_sizes), figsize=(6 * len(available_sizes), 10), sharey=True)
        if len(available_sizes) == 1:
            axes = [axes]
            
        # Zamiana czasów 0.0 na minimalną wartość (1e-6) by uniknąć błędów ze skalą logarytmiczną
        df['Time'] = df['Time'].apply(lambda x: 1e-6 if x <= 0 else x)
        vmin = df['Time'].min()
        vmax = df['Time'].max()
        
        for ax, size in zip(axes, available_sizes):
            df_size = df[df['Size'] == size]
            pivot_df = df_size.pivot(index='Operation', columns='Database', values='Time')
            
            # Wymuszenie stałej kolejności kolumn
            cols = [db for db in DATABASES if db in pivot_df.columns]
            pivot_df = pivot_df[cols]
            
            sns.heatmap(
                pivot_df, 
                ax=ax, 
                annot=True, 
                fmt=".4g", # g dla lepszego formatowania skrajnych liczb 
                cmap="YlOrRd", # żółty (najszybciej) -> czerwony (najwolniej)
                norm=LogNorm(vmin=vmin, vmax=vmax),
                cbar=(ax == axes[-1]), # tylko ostatni subplot ma pasek legendy
                cbar_kws={'label': 'Czas wykonania (s) [skala logarytmiczna]'} if ax == axes[-1] else None,
                linewidths=.5
            )
            ax.set_title(f'Zbiór danych: {size}', fontsize=14)
            ax.set_ylabel('Operacja (Scenariusz testowy)' if ax == axes[0] else '')
            ax.set_xlabel('Silnik bazodanowy')
            ax.tick_params(axis='y', rotation=0)
        
        title_suffix = "bez wdrożonych indeksów" if mode == 'without_indexes' else "po wdrożeniu indeksów"
        plt.suptitle(f'Heatmapa wydajności operacji - {title_suffix}', fontsize=18, y=1.02)
        plt.tight_layout()
        
        # Zapis do głównego folderu
        out_name = f'heatmap_{mode}.png'
        plt.savefig(out_name, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Wygenerowano pomyślnie plik: {out_name}")

if __name__ == '__main__':
    data = load_data()
    if data:
        plot_heatmaps(data)
        print("Zakończono proces generowania.")
    else:
        print("Błąd: Nie znaleziono danych (uruchom skrypt w tym samym folderze co pliki .json)")
