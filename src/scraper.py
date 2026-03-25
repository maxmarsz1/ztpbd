import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import os
import random

def get_item_links(driver, url):
    print(f"Pobieranie głównej listy ze strony: {url}...")
    success = False
    retries = 0
    while not success and retries < 5:
        driver.get(url)
        time.sleep(random.uniform(3, 6)) # Czekanie na Cloudflare
        
        # Proste sprawdzenie Cloudflare
        if "Just a moment..." in driver.title or "Attention Required" in driver.title:
            print(" Napotkano wyzwanie Cloudflare. Próba przejścia...")
            time.sleep(10)
            if "Just a moment..." in driver.title:
                retries += 1
                continue
                
        # Sprawdzanie czy strona zwróciła 403 (Zablokowano)
        if "403 Forbidden" in driver.page_source or ("Cloudflare" in driver.title and "blocked" in driver.page_source.lower()):
            print(f" Wynik 403 (Zablokowano pobieranie) dla strony głównej. Dłuższe ostudzenie...")
            retries += 1
            time.sleep(random.uniform(10, 20))
            continue
            
        success = True
            
    if not success:
        print("Nie powiodło się pobranie głównej strony.")
        return []
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
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

def scrape_item_details(driver, item):
    success = False
    retries = 0
    while not success and retries < 5:
        try:
            driver.get(item['url'])
            # Krótka pauza "ludzka" by nie przeciążać
            time.sleep(random.uniform(1.5, 3))
            
            if "Just a moment..." in driver.title or "Attention Required" in driver.title:
                print(f" Wynik: weryfikacja Cloudflare dla {item['name']}...")
                time.sleep(10)
                if "Just a moment..." in driver.title:
                    retries += 1
                    continue
            
            if "403 Forbidden" in driver.page_source or ("Cloudflare" in driver.title and "blocked" in driver.page_source.lower()):
                print(f" Wynik 403 dla {item['name']}. Kwarantanna IP... Zwalniam tempo.")
                time.sleep(random.uniform(45, 90))
                retries += 1
            else:
                success = True
        except Exception as e:
            print(f" Błąd pobierania {item['name']}: {e}")
            time.sleep(1)
            retries += 1
            
    if not success:
        print(f" Nie udało się pobrać {item['name']} po kilku próbach.")
        return None
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
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
            text = p.text.strip()
            if not text or len(text) < 30:
                continue
            if p.find('i') and len(text) < 80:
                continue
                
            desc_texts.append(text)
            if len(desc_texts) >= 2:
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
        return
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Błąd podczas zapisu pliku JSON: {e}")

def main():
    print("================== SCARPER TERRARIA WIKI ==================")
    print("Tryb Tradycyjny. Silnik: Selenium (undetected-chromedriver)\n")
    
    options = uc.ChromeOptions()
    options.headless = False  # Zalecane widoczne okno do przejścia pierwszego Cloudflare
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Do zablokowania ładowania obrazków itd. (opcjonalne, w uc bywa pomocne)
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheet": 2,
        "profile.managed_default_content_settings.fonts": 2
    }
    options.add_experimental_option("prefs", prefs)

    driver = None
    try:
        # Odpalamy przeglądarkę
        print("Uruchamianie przeglądarki Selenium (może potrwać chwilę)...")
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        links_cache_file = "item_links_cache.json"
        if os.path.exists(links_cache_file):
            print(f"[!] Wczytywanie zbuforowanej listy linków z {links_cache_file}...")
            with open(links_cache_file, "r", encoding="utf-8") as f:
                item_links = json.load(f)
        else:
            item_links = get_item_links(driver, "https://terraria.wiki.gg/wiki/Item_IDs")
            if item_links:
                with open(links_cache_file, "w", encoding="utf-8") as f:
                    json.dump(item_links, f, ensure_ascii=False, indent=4)
                
        if not item_links:
            print("Brak linków do pobrania. Anuluję.")
            return

        print(f"\nZebrano adresy URL do {len(item_links)} przedmiotów.")
        
        TEST_LIMIT = 500
        item_links_test = item_links[:TEST_LIMIT]
        print(f"Ograniczono pobieranie do pierwszych {TEST_LIMIT} elementów na cel testu...\n")
        
        scraped_full_data = []
        seen_ids = set()
        
        target_file = "scraped_items_selenium.json"
        if os.path.exists(target_file):
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    scraped_full_data = json.load(f)
                    seen_ids = {item["id"] for item in scraped_full_data}
                print(f"[!] Wznowiono pracę: załadowano już {len(seen_ids)} gotowych przedmiotów z pamięci.")
            except Exception:
                pass
        
        start_time = time.time()
        processed_so_far = 0
        
        items_to_process = [item for item in item_links_test if item["id"] not in seen_ids]
        
        print("Rozpoczynam sekwencyjne pobieranie (Selenium korzysta z 1 wątku)...")
        
        try:
            for item in items_to_process:
                details = scrape_item_details(driver, item)
                if details:
                    scraped_full_data.append(details)
                    seen_ids.add(item["id"])
                    
                processed_so_far += 1
                elapsed = time.time() - start_time
                avg_time = elapsed / processed_so_far
                remaining_items = len(items_to_process) - processed_so_far
                remaining_secs = remaining_items * avg_time
                m, s = divmod(int(remaining_secs), 60)
                eta_str = f"[ETA: {m}m {s}s]"
                
                print(f"{eta_str} [{processed_so_far}/{len(items_to_process)}] Zakończono: {item['name']}")
                
                if len(scraped_full_data) % 10 == 0:
                    save_to_json(scraped_full_data, target_file)
                    
        except KeyboardInterrupt:
            print("\n\n[!] Otrzymano sygnał przerwania! Zostało wstrzymane przez Ciebie.")
            print("[!] Zapisuję dotychczas pobrane elementy przed wyjściem...")
            
        save_to_json(scraped_full_data, target_file)
        print(f"\nScrapowanie zakończone. Wynik w pliku `{target_file}`.")
    
    except Exception as e:
        print(f"Niespodziewany błąd programu: {e}")
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()
