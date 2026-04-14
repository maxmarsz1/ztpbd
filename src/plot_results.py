import os
import json
import argparse
import matplotlib.pyplot as plt
import numpy as np

def generate_plots(profile):
    filename = f"benchmark_results_{profile}.json"
    if not os.path.exists(filename):
        print(f"Brak pliku wyników {filename}. Uruchom benchmark.py z tym profilem.")
        return

    with open(filename, 'r') as f:
        data = json.load(f)

    # Przygotowanie folderu na wykresy
    out_dir = f"../sprawozdanie/wykresy_{profile}"
    os.makedirs(out_dir, exist_ok=True)

    without_idx = data["without_indexes"]
    with_idx = data["with_indexes"]

    # Grupowanie scenariuszy CRUD
    crud_groups = {'C': [], 'R': [], 'U': [], 'D': []}
    for scenario in without_idx.keys():
        category = scenario[0] # C, R, U, D
        if category in crud_groups:
            crud_groups[category].append(scenario)

    db_systems = ['postgres', 'mysql', 'redis', 'mongo']
    colors = ['#3366cc', '#dc3912', '#ff9900', '#109618']

    def autolabel(rects, ax):
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.4f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, rotation=90)

    # Wykresy dla poszczególnych kategorii CRUD z indeksami i bez
    for cat_name, scenarios in crud_groups.items():
        if not scenarios: continue
        
        x = np.arange(len(scenarios))
        width = 0.2

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))

        # Bez indeksów
        for i, db in enumerate(db_systems):
            times = [without_idx[sc].get(db, 0.0) for sc in scenarios]
            rects = ax1.bar(x + i*width - 1.5*width, times, width, label=db.upper(), color=colors[i])
            autolabel(rects, ax1)

        ax1.set_ylabel('Czas (sekundy)')
        ax1.set_title(f'Kategoria {cat_name} - BEZ Indeksów ({profile})')
        ax1.set_xticks(x)
        ax1.set_xticklabels(scenarios, rotation=45, ha="right")
        ax1.legend()
        ax1.grid(axis='y', linestyle='--', alpha=0.7)

        # Z indeksami
        for i, db in enumerate(db_systems):
            times = [with_idx[sc].get(db, 0.0) for sc in scenarios]
            rects = ax2.bar(x + i*width - 1.5*width, times, width, label=db.upper(), color=colors[i])
            autolabel(rects, ax2)

        ax2.set_ylabel('Czas (sekundy)')
        ax2.set_title(f'Kategoria {cat_name} - Z Indeksami ({profile})')
        ax2.set_xticks(x)
        ax2.set_xticklabels(scenarios, rotation=45, ha="right")
        ax2.legend()
        ax2.grid(axis='y', linestyle='--', alpha=0.7)

        plt.tight_layout()
        plt.savefig(f"{out_dir}/wykres_{cat_name}.png")
        plt.close()

    print(f"Wygenerowano wykresy dla profilu {profile} w folderze wyjściowym sprawozadnie/wykresy_{profile}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=['maly', 'sredni', 'duzy'], default='maly')
    args = parser.parse_args()
    generate_plots(args.profile)
