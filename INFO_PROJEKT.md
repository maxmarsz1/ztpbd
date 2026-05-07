# Architektura Projektu ZTBD

Projekt jest dobrze zorganizowany i odpowiada za pełen cykl życia testów: od postawienia środowiska, przez generowanie danych, aż po same testy i wykresy. Poniżej znajduje się opis najważniejszych plików i tego, co się w nich znajduje.

---

## 1. Środowisko i Bazy Danych

* **`docker-compose.yml`**  
  Definiuje i uruchamia 4 kontenery z bazami danych: MySQL, PostgreSQL 17, Redis 7 oraz MongoDB. Bazy te mają zmapowane wolumeny (katalogi `*_data`), dzięki czemu dane są persystentne i przetrwają restarty kontenerów.
  
* **`src/init_db.py`**  
  Skrypt inicjalizacyjny, który uruchamia się na początku. Jego zadaniem jest stworzenie struktury (schematów) dla baz relacyjnych – tworzy tabele, klucze główne (PK) i klucze obce (FK).

---

## 2. Zasilanie Danymi

* **`src/generate_data.py`**  
  Główny generator danych ("kombajn"). Wykorzystuje bibliotekę `Faker` do generowania realistycznych danych dla 12 różnych tabel o tematyce gry RPG (np. środowiska, NPC, warianty przeciwników, statystyki, przedmioty). Skrypt ładuje dane **współbieżnie** i potrafi korzystać z predefiniowanych profili wielkościowych:
  * `maly` (ok. 10 tys. rekordów)
  * `sredni` (ok. 100 tys. rekordów)
  * `duzy` (kilka/kilkanaście milionów rekordów)

* **`src/main.py`**  
  Plik spinający całe środowisko. Jego logika to:
  1. Poczekać na uruchomienie się wszystkich baz (mechanizm *wait-for-it*).
  2. Wywołać `init_db.py`.
  3. Uruchomić generator danych `generate_data.py`.
  4. Przeliczyć rekordy w każdej bazie (weryfikacja integralności).
  5. Zrzucić dane z pamięci RAM baz nierelacyjnych (Redis/Mongo) na dysk, żeby zapewnić im trwałość.

---

## 3. Testy Wydajnościowe (Benchmark)

* **`src/benchmark.py`**  
  Serce testów wydajnościowych. Łączy się ze wszystkimi bazami i wykonuje testy w dwóch fazach: najpierw **bez indeksów** (`NO_INDEX`), a po ich sztucznym utworzeniu **z indeksami** (`WITH_INDEX`). W pliku znajduje się **24 scenariuszy testowych** podzielonych na klasyczne operacje CRUD (Create, Read, Update, Delete). Każdy scenariusz odpala się 3 razy (w celu wyciągnięcia wiarygodnej średniej).

### Rozpisane Scenariusze (CRUD) z `benchmark.py`:

**CREATE (Zapis/Wstawianie):**
1. **C1_SingleInsert** - Wstawienie pojedynczego wiersza (np. nowy typ AI).
2. **C2_BatchInsert10** - Paczkowe wstawienie małej porcji 10 rekordów.
3. **C3_BulkInsert1000** - Masowe, zoptymalizowane wstawienie 1000 rekordów.
4. **C4_DependentInsert** - Wstawienie powiązane, czyli dodanie dwóch zależnych od siebie wierszy (np. Receptura i jej Składnik).
5. **C5_Upsert** - Wstawienie z aktualizacją w przypadku kolizji klucza (`ON CONFLICT DO UPDATE` / `$set`).
6. **C6_DeepNestedInsert** - Głębokie wstawianie (w bazach relacyjnych to kilka osobnych `INSERT`, a w Mongo dodanie jednego głęboko zagnieżdżonego dokumentu).

**READ (Odczyt/Pobieranie):**
7. **R1_ReadByPK** - Klasyczne, szybkie wyszukiwanie po kluczu głównym (ID).
8. **R2_ReadFilterSimple** - Proste filtrowanie danych (np. cena przedmiotu `> 100`).
9. **R3_ReadFilterRange** - Wyszukiwanie zakresowe (`BETWEEN`) po kilku parametrach.
10. **R4_AggregateCount** - Agregacja danych (grupowanie po typie i liczenie rekordów za pomocą `GROUP BY`).
11. **R5_JoinSmall** - Złączenie dwóch tabel (`JOIN`) lub w Mongo operator `$lookup`.
12. **R6_ComplexQuery** - Skomplikowane zapytanie, które pobiera dane z 3 połączonych tabel, a następnie grupuje, liczy średnią i sortuje. W bazie MongoDB nałożono na to limit czasowy (20 sekund), żeby pokazać ograniczenia architektury w zapytaniach z naturalnymi złączeniami.

**UPDATE (Aktualizacja):**
13. **U1_UpdateSingle** - Aktualizacja jednego atrybutu (np. inkrementacja ceny przedmiotu).
14. **U2_UpdateMath** - Mnożenie matematyczne bezpośrednio w bazie (np. podwójne obrażenia dla przedziału kluczy).
15. **U3_UpdateInCondition** - Masowa zmiana dla ściśle wskazanych kluczy (`WHERE id IN (...)`).
16. **U4_ReplaceFull** - Pełne zastąpienie istniejącego rekordu nowymi danymi.
17. **U5_UpdateWithJoinSubq** - Aktualizacja korzystająca z podzapytania (`SELECT` wewnątrz `UPDATE`).
18. **U6_BulkCaseWhenUpdate** - Bardzo zaawansowana zmiana zbiorcza korzystająca z instrukcji warunkowej `CASE WHEN`.

**DELETE (Usuwanie):**
19. **D1_DeleteSingle** - Usunięcie pojedynczego rekordu po ID.
20. **D2_DeleteByCondition** - Usunięcie wszystkich wierszy spełniających prosty warunek.
21. **D3_DeleteRange** - Usunięcie szerokiego zakresu po ID.
22. **D4_DeleteSubquery** - Kaskadowe/sprytne usunięcie danych na bazie podzapytania z innej tabeli.
23. **D5_DeleteBatchedControlled** - Bezpieczne usuwanie porcjami (np. ograniczone przez `LIMIT 50`).
24. **D6_DeleteAllTruncate** - Pełne wyczyszczenie tabeli z danych (operacja typu `TRUNCATE`).

---

## 4. Wyniki i Raportowanie

* Na sam koniec `benchmark.py` zapisuje rezultaty czasowe w formie plików **JSON** (np. `benchmark_results_maly.json`).
* Dodatkowo zapisuje szczegóły silników bazodanowych pokazujące sposób przetwarzania zapytań (plany `EXPLAIN`) do plików `.txt`. Służą one potem w dokumencie do udowodnienia różnic w "planie zapytań" pomiędzy bazami z indeksami i bez nich.
* Plik **`src/plot_results.py`** służy do wyciągnięcia danych z wygenerowanych `.json`ów i generowania wykresów wizualizujących wyniki testów dla łatwego dołączenia do sprawozdania.
