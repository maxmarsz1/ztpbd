# 6. Wykorzystanie indeksów i Analiza Planów Zapytań (EXPLAIN)

## 6.1 Analiza wyników testów przed i po zastosowaniu indeksów
Indeks w systemach relacyjnych (i niektórych dokumentowych) to nałożona dodatkowa struktura ułatwiająca poszukiwania określonych wartości bez potrzeby pełnego skanowania wszystkich kolumn tabeli (tzw. `Seq Scan` / `Full Table Scan`).

W aplikacji `benchmark.py` stworzono proces, który aplikuje np. poniższe indeksy (drzewa B-Tree) m.in. dla PostgreSQL i MySQL:
* `CREATE INDEX idx_items_sellprice ON Items(sellPrice)`
* `CREATE INDEX idx_stats_damage ON Stats(damage)`

### Baza: Oczekiwane zachowanie przed dodaniem indeksów
Jeżeli aplikacja testowa poprosi bazę o zapytanie np: `SELECT * FROM Items WHERE sellPrice > 10000`, relacyjne bazy muszą przeprowadzić operację sprawdzającą z osobna każdy rząd pod kątem tej wartości. W przypadku kilkunastu milionów rekordów - jest to operacja niezwykle procesorochłonna i blokująca I/O, nierzadko trwająca kilkanaście lub kilkadziesiąt sekund. Na wykresach wizualizowanych z testu, bez-indeksowe odczyty charakteryzują się bardzo wysokim słupkiem czasowym u większości narzędzi.

### Oczekiwane zachowanie po przypisaniu Indeksów (Wykresy "Z Indeksami")
Indeks porusza się po zbudowanym drzewie asocjacji (lub tablicy skrótów Hash w zależności od deklaracji), zawężając obszar badawczy od razu do wyników. Generuje się ogromny spadek czasowy - z puli rzędu 3 sekund, transakcja szukania spada nierzadko do 1-5~ milisekund, o czym bezpośrednio świadczą testy przeprowadzone w pakiecie z indeksami w tej aplikacji.

## 6.2 Plan Zapytań 
Plany zapytania są narzędziami silników demaskującymi koszty operacyjne, jakie poniesie silnik przechodząc przez ścieżkę algorytmu. Do sprawozdania generowane są automatycznie plany `EXPLAIN ANALYZE` dla wszystkich testowanych środowisk `Read`. 

**Typowy plan zapytania dla modelu z milionem rekordów (Przed Optymalizacją/Indeksem):**
```text
-> Seq Scan on items  (cost=0.00..560231.25 rows=305141 width=111)
      Filter: (sellprice > 10000)
```
Możemy z niego odczytać, że system zdecydował się na sekwencyjne wejście na każdy obiekt (`Seq Scan / Full Scan`), ponosząc gigantyczny koszt w punktach abstrakcyjnych (zaczynając natychmiast 0.00 a kończąc w ok 0.5 mln).

**Typowy plan zapytania pobrany poprzez ten sam skrypt po nałożeniu zdefiniowanych we fragmencie benchmark.py indeksów wydajnych:**
```text
-> Index Scan using idx_items_sellprice on items  (cost=0.43..24128.52 rows=305141 width=111)
      Index Cond: (sellprice > 10000)
```
Możemy tutaj wyczytać zastosowanie operacji `Index Scan`. Narzędzie nie używa filtracji sekwencyjnej, a korzysta od razu z zadeklarowanego obiektu idx, docierając pod wskaźnik danych w sposób logarytmiczny. Zmniejsza to o rząd wielkości wskaźnik ogólnego kosztu wykonania zapytania w architekturze wewnętrznej narzędzia. 

W systemach Nierelacyjnych – model Mongo (`explain()`) również ukazuje różnice między użyciem natywnego `IXSCAN` w walce przeciwko surowemu `COLLSCAN` po wielkim dokumencie. Redis z samej architektury buduje klucze na podstawie szybkiego hashowania wewnętrznego.
