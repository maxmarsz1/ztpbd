from bs4 import BeautifulSoup
from scrapling import StealthyFetcher
import json
import time

def get_item_links(url):
    """Pobiera wszystkie unikalne linki do podstron przedmiotów przy użyciu frameworka Scrapling."""
    print(f"Pobieranie głównej listy ze strony: {url}...")
    
    # Scrapling StealthyFetcher - omija Cloudflare automatycznie!
    page = StealthyFetcher.fetch(url, real_chrome=True)
    
    # Przekazujemy body strony do BS4 dla gwarancji stabilnego parsowania tekstów
    soup = BeautifulSoup(page.body, 'html.parser')
    
    tables = soup.find_all('table', class_=['terraria', 'wikitable'])
    links = []
    
    if not tables:
        print("Nie znaleziono tabel ze spisem przedmiotów.")
        return links
        
    for table in tables:
        for row in table.find_all('tr')[1:]:
            cols = row.find_all(['td', 'th'])
            if len(cols) >= 5:
                # Najczęściej link główny znajduje w pierwszej lub drugiej kolumnie
                name_elem = cols[1].find('a') if len(cols) > 1 else None
                if not name_elem:
                    name_elem = cols[0].find('a')
                    
                if name_elem and name_elem.has_attr('href'):
                    href = name_elem['href']
                    name = name_elem.text.strip()
                    
                    if href.startswith('/wiki/') and "File:" not in href and "Category:" not in href:
                         links.append({
                             "name": name, 
                             "url": "https://terraria.wiki.gg" + href
                         })
                         
    # Usuwanie duplikatów
    unique_links = []
    seen = set()
    for item in links:
        clean_name = item['name'].split("Internal ")[0].strip()
        if item['url'] not in seen:
            unique_links.append({"name": clean_name, "url": item['url']})
            seen.add(item['url'])
            
    return unique_links

def scrape_item_details(item):
    """Wchodzi w adres URL przedmiotu używając Scrapling i pobiera z niego szczegóły (opis i infobox)."""
    print(f"-> Skrapowanie: {item['name']}")
    
    # Błyskawiczny fetch ze StealthyFetcher
    try:
        page = StealthyFetcher.fetch(item['url'], real_chrome=True)
    except Exception as e:
        print(f" Błąd pobierania {item['name']}: {e}")
        return None
    
    soup = BeautifulSoup(page.body, 'html.parser')
    
    item_data = {
        "name": item['name'],
        "url": item['url'],
        "description": "",
        "stats": {}
    }
    
    # POBIERANIE OPISU
    content_area = soup.find('div', class_='mw-parser-output')
    if content_area:
        paragraphs = content_area.find_all('p', recursive=False)
        desc_texts = []
        for p in paragraphs[:2]: 
            text = p.text.strip()
            if len(text) > 10:
                desc_texts.append(text)
        item_data['description'] = " ".join(desc_texts).strip()
        
    # POBIERANIE STATYSTYK
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

def save_to_json(data, filename="scraped_swords.json"):
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
        # Krok 1: Pobierz listę linków
        item_links = get_item_links("https://terraria.wiki.gg/wiki/Swords")
        print(f"\nZebrano adresy URL do {len(item_links)} unikalnych przedmiotów.")
        
        scraped_full_data = []
        
        # Krok 2: Odwiedź każdą ze stron omijając zabezpieczenia z Scrapling
        for i, item in enumerate(item_links):
            print(f"\n[{i+1}/{len(item_links)}] ", end="")
            details = scrape_item_details(item)
            if details:
                scraped_full_data.append(details)
            
        save_to_json(scraped_full_data)
        
    except Exception as e:
        print(f"Niespodziewany błąd programu: {e}")
