from bs4 import BeautifulSoup
from scrapling import StealthyFetcher
import json
import time
from concurrent.futures import ThreadPoolExecutor

def get_item_links(url):
    """Pobiera wszystkie unikalne linki do podstron przedmiotów wraz z ich ID."""
    print(f"Pobieranie głównej listy ze strony: {url}...")
    
    success = False
    page = None
    retries = 0
    import random
    while not success and retries < 5:
        page = StealthyFetcher.fetch(url, real_chrome=True)
        if hasattr(page, 'status') and page.status == 403:
            print(f" Wynik 403 (Zablokowano pobieranie) dla strony głównej. Dłuższe ostudzenie...")
            time.sleep(random.uniform(15, 30))  # Dłuższe oczekiwanie by spuścić z tonu
            retries += 1
        else:
            success = True
            
    if not success or not page:
        print("Nie powiodło się pobranie głównej strony.")
        return []
    
    soup = BeautifulSoup(page.body, 'html.parser')
    
    tables = soup.find_all('table')
    links = []
    
    if not tables:
        print("Nie znaleziono tabel ze spisem przedmiotów.")
        return links
        
    table = tables[0]
    for row in table.find_all('tr')[1:]:
        cols = row.find_all(['td', 'th'])
        if len(cols) >= 3:
            id_num = cols[0].text.strip()
            name_elem = cols[1].find('a')
            
            if name_elem and name_elem.has_attr('href'):
                href = name_elem['href']
                name = name_elem.text.strip()
                
                if href.startswith('/wiki/'):
                     links.append({
                         "id": id_num,
                         "name": name, 
                         "url": "https://terraria.wiki.gg" + href
                     })
                     
    return links

def scrape_item_details(item):
    """Wchodzi w adres URL przedmiotu i pobiera z niego szczegóły (opis i infobox)."""
    import random
    time.sleep(random.uniform(5, 12))  # Powolne działanie imitujące człowieka przed Cloudflare
    print(f"-> Skrapowanie [{item['id']}]: {item['name']}")
    
    success = False
    page = None
    retries = 0
    while not success and retries < 5:
        try:
            page = StealthyFetcher.fetch(item['url'], real_chrome=True)
            if hasattr(page, 'status') and page.status == 403:
                print(f" Wynik 403 (Zablokowano pobieranie) dla {item['name']}. Oczekiwanie MOCNO dłuższej chwili (kwarantanna IP)...")
                time.sleep(random.uniform(30, 60)) # Wymuszona "ludzka" przerwa
                retries += 1
            else:
                success = True
        except Exception as e:
            print(f" Błąd pobierania {item['name']}: {e}")
            time.sleep(3)
            retries += 1
            
    if not success or not page:
        print(f" Nie udało się pobrać {item['name']} po kilku próbach.")
        return None
    
    soup = BeautifulSoup(page.body, 'html.parser')
    
    item_data = {
        "id": item['id'],
        "name": item['name'],
        "url": item['url'],
        "description": "",
        "stats": {}
    }
    
    content_area = soup.find('div', class_='mw-parser-output')
    if content_area:
        paragraphs = content_area.find_all('p', recursive=False)
        desc_texts = []
        for p in paragraphs:
            # Pomijanie cytatów, które często pojawiają się na samej górze i psuły pobranie
            text = p.text.strip()
            if not text or len(text) < 30:
                continue
            if p.find('i') and len(text) < 80:
                continue
                
            desc_texts.append(text)
            if len(desc_texts) >= 2:  # Bierzemy max 2 rzeczowe akapity
                break
                
        item_data['description'] = " ".join(desc_texts).strip()
        
    stat_tables = soup.find_all('table', class_='stat')
    for table in stat_tables:
        for row in table.find_all('tr'):
            th = row.find('th')
            td = row.find('td')
            if th and td:
                key = th.text.strip()
                val = td.text.strip().replace("\n", " ").strip()
                if key and val:
                    item_data['stats'][key] = val
                
    return item_data

def save_to_json(data, filename="scraped_items.json"):
    if not data:
        print("Brak danych do zapisania.")
        return
        
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\nDane zostały pomyślnie zapisane do pliku: {filename}")
    except Exception as e:
        print(f"Błąd podczas zapisu pliku JSON: {e}")

if __name__ == "__main__":
    print("================== SCARPER TERRARIA WIKI ==================")
    print("Tryb Framework. Silnik: Scrapling (D4Vinci)\n")
    
    try:
        item_links = get_item_links("https://terraria.wiki.gg/wiki/Item_IDs")
        print(f"\nZebrano adresy URL do {len(item_links)} przedmiotów.")
        
        # OGRANICZNIK TESTOWY - dla demonstracji tylko kilka elementów
        TEST_LIMIT = 5
        item_links_test = item_links[:TEST_LIMIT]
        print(f"Ograniczono pobieranie do pierwszych {TEST_LIMIT} elementów na cel testu...\n")
        
        # Wczytywanie ewentualnego postępu, by nie zaczynać od zera przy restarcie!
        import os
        scraped_full_data = []
        seen_ids = set()
        
        target_file = "scraped_items_test.json"
        if os.path.exists(target_file):
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    scraped_full_data = json.load(f)
                    seen_ids = {item["id"] for item in scraped_full_data}
                print(f"[!] Wznowiono pracę: załadowano już {len(seen_ids)} gotowych przedmiotów z pamięci.")
            except Exception:
                pass
        
        # Skrapowanie sekwencyjne (jeden po drugim)
        try:
            for i, item in enumerate(item_links_test):
                if item["id"] in seen_ids:
                    # Pomijamy pobrane wcześniej, żeby skrypt był super-skalowalny i ignorował duplikaty
                    continue
                    
                print(f"\n[{i+1}/{len(item_links_test)}] ", end="")
                details = scrape_item_details(item)
                if details:
                    scraped_full_data.append(details)
                    seen_ids.add(item["id"])
                    
                # Auto-zapis do bazy co każdych 10 prawidłowo pobranych przedmiotów 
                if len(scraped_full_data) % 10 == 0:
                    save_to_json(scraped_full_data, target_file)
                    
        except KeyboardInterrupt:
            print("\n\n[!] Otrzymano sygnał przerwania! Zostało wstrzymane przez Ciebie.")
            print("[!] Zapisuję dotychczas pobrane elementy przed wyjściem...")
            
        # Zapis końcowy / ratunkowy
        save_to_json(scraped_full_data, target_file)
        print("Scrapowanie przerwane lub zakończone. Możesz obejrzeć plik `scraped_items_test.json`.")
        
    except Exception as e:
        print(f"Niespodziewany błąd programu: {e}")
