# 4. Modele i Struktury Zbioru Danych 
Spreparowane przez system zbiory danych posiadają model uniwersalny osadzony w obrębie rozległej bazy naśladującej środowiska gier MMORPG.

## 4.1 Modele Relacyjne (PostgreSQL, MySQL)
Architektura w systemach SQL posiada strukturę mocno znormalizowaną. Projekt wykorzystuje łącznie 12 spoiście obramowanych tabel kluczami głównymi i obcymi:
1. **Environments** (`id`, `name`, `description`) – Środowiska biograficzne gry.
2. **AITypes** (`id`, `name`, `description`) – Logika behawioralna sterowania jednostek bazy.
3. **NPCs** (`id`, `typeID`) – Główna relacyjna tablica określająca neutralnych reydentów powiązanych z bazą sztucznej inteligencji.
4. **NPCEnvironments** (`id`, `npcID`, `environmentID`) – Tabela łącząca w system N:M, lokująca w lokacjach.
5. **EnemyVariants** (`id`, `npcID`, `AITypeID`, `type`, `mode`) – Poszerzona wersja rekordu określająca tryb zmutowanego NPC.
6. **EnemyVariantStats** (`id`, `variantID`, `health`, `damage`, `defense`, `coins`)
7. **NPCSounds** (`id`, `npcID`, `url`) 
8. **Stats** (`id`, `itemID`, `damage`, `knockback`, `criticalChance`, `useTime`, `mana`, `velocity`, `tooltip`, `defense`, ...)
9. **Items** (`id`, `name`, `description`, `type`, `material`, `statsID`, `sellPrice`) – Główna tabela Przedmiotów, posiadująca FK do Stats.
10. **itemsRecipies** (`id`, `itemID`, `craftingStation`) 
11. **recipies** (`id`, `itemRecipieID`, `itemID`, `amount`) – Powiązanie rekordu tworzenia z docelowymi przedmiotami (składniki N:M).
12. **EnemyDrops** (`id`, `variantID`, `itemID`, `rate`) – Określa, jakie elementy Items mogą zostać wygenerowane po zniszczeniu EnemyVariant.

## 4.2 Model Dokumentowy (MongoDB)
System NoSQL reprezentowany m.in. przez Mongo obala częściowo formę znormalizowanych relacji na korzyść zagłębianych kolekcji. O ile części obiektów przenoszone są jako relacje `1:1` ze zbiorów źródłowych RDBMS na proste kolekcje `id`, tak scenariusze głębokie w teście generują obiekty strukturalnie zagłębiane np: `{'typeID': 1, 'variant': {'type': 'M', 'stats': {'health': 10}}}`. Modele dokumentowe wykazują gigantyczną przewagą na wbudowanych i elastycznych metadanych nieobarczonych wymaganymi klauzulami tabel.

## 4.3 Model Pamięci RAM: Klucz-Wartość (Redis)
Struktury tabel relacyjnych kompilowane do Redis przybrały format obiektów typu `HASH`.  Przykładowo pole dla Items zapisane jest na dysku Redis w formie klucza `Items:1255`. Dostęp do każdego dokumentu wynosi w takim schemacie O(1), jednak filtrowanie wymaga stosowania nieoptymalnego mapowania lub ręcznych Set-ów/List przetrzymujących tagi.

---

# 5. Opis Aplikacji Testowej do Zarządzania Badaniami (Benchmark)
**Wymagania Techniczne Wdrożenia:**
Aplikacja została zaprogramowana w wysokopoziomowym języku interpretowanym **Python (wersja 3.11)**. Jako serwery ucieleśniające podłoże, wykorzystano skonteneryzowane obrazy narzędzia **Docker**.  Aplikacja bazuje na sterownikach bezpośrednich dla każdej testowanej architektury: `psycopg2`, `mysql-connector-python`, `redis`, oraz potężnej bibliotece `pymongo`.

**Mechanizm działania - Aplikacja dzieli się na dwa cykle i składa z 3 programów modułowych:**
1. **Generator Danych** (`generate_data.py` / `main.py`): Posiada mechanizm operacji w wirtualnej pamięci pul z użyciem `Faker` oraz wstrzykujący algorytmy do bazy bez narzutu sprawdzania Integralności Kluczy Obcych w celu drastycznego przyspieszenia obciążenia pre-testowego. Możliwość generowania na profil `maly(10k)`, `sredni(100k)` i `duzy(10M+)`.
2. **Obiekt Badawczy (Benchmark Test)** (`benchmark.py`): Jądro uruchalmiające 24 wyselekcjonowane w skrypcie bloki (po 6 badawczych na każdą operację **C R U D**). Skrypt automatycznie łączy się z 4 docelowymi dyskami, bada 24 scenariusze w pętli `N=3`, pozyskując informację o `czasie` transakcji oraz pobierając `EXPLAIN zapytania` jeżeli jest dostępne dla tego języka bazodanowego. Po przebiegu skrypt zdejmuje indeksy relacyjne z baz i ponawia ten wielominutowy proces.
3. **Logika i Wykres** (`plot_results.py`): Autorska integracja algorytmów transformacji zaopatrzona w technologię `Matplotlib` do wizualizowania zrzutów czasowych transakcji generująca przejrzyste różnice wydajnościowe silników wg wielkości instrukcji i zastosowania profilu indeksowania.
