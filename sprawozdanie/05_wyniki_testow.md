# 7. Wyniki Testów i Rozszerzona Analiza (Podsumowanie)

Zautomatyzowane testy z puli 24 ustrukturyzowanych skryptów na potężnych modelach badawczych udowodniły kilka interesujących zależności. Pomiary uśrednione z 3 transakcji (na każdy scenariusz w każdej z baz) można poddać weryfikacji. 

## 7.1 Analiza wyników testów wydajnościowych (Kategoria C – Wstawianie)
**Wnioski z wykresów (`wykres_C.png`):**
W operacjach pojedynczego wstawiania (C1) oraz paczkowych (C2, C3) dominującą prędkością wykazuje się **Redis**, co wynika bezpośrednio z jego natury – przechowywania i operowania na danych w pamięci RAM (in-memory). **MongoDB** radzi sobie znakomicie ze wstawianiem obszernych, głęboko zagnieżdżonych struktur (scenariusz C6), ponieważ operacja ta wymaga zapisania pojedynczego dokumentu BSON. W bazach relacyjnych (**PostgreSQL**, **MySQL**) głębokie wstawianie wymaga wykonania serii powiązanych instrukcji `INSERT` z dbałością o klucze obce, co generuje większy narzut czasowy. Wykresy "Z indeksami" wyraźnie pokazują również klasyczne zjawisko występujące w bazach danych – narzut indeksowania. Bazy MySQL i Postgres notują niewielki spadek wydajności zapisu, ponieważ każda operacja `INSERT` wymaga teraz dodatkowej aktualizacji struktury drzewiastej (B-Tree) samego indeksu. Zyskują one jednak na maksymalnym bezpieczeństwie danych i zachowaniu własności ACID.

## 7.2 Analiza wyników testów wydajnościowych (Kategoria R – Odczyt)
**Wnioski z wykresów (`wykres_R.png`):**
Odczyt to kategoria, która najlepiej uwydatnia architektoniczną siłę poszczególnych rozwiązań. Odczyty bezpośrednie po kluczu głównym (R1) są błyskawiczne i skalują się znakomicie w każdym z silników. 
Prawdziwe różnice widać przy złożonym zapytaniu (R6_ComplexQuery). Złączenie trzech tabel ze zliczaniem, wyliczaniem średniej i sortowaniem wykonuje się w silnikach **PostgreSQL** i **MySQL** w ułamku sekundy, dzięki wysoce zoptymalizowanym silnikom przetwarzania zapytań relacyjnych (Query Planners). Z kolei **MongoDB**, jako nierelacyjna baza dokumentowa, drastycznie przegrywa w tym scenariuszu (osiągając kary rzędu dziesiątek/setek sekund). Operatory takie jak `$lookup` dla relacji wirtualnych okazują się niezwykle kosztowne, jeśli dokumenty nie zostały na etapie projektowania osadzone (embedded) bezpośrednio w sobie. Po włączeniu indeksów czas wyszukiwania zakresowego (R3) oraz agregacji (R4) zauważalnie skraca się dla baz relacyjnych.

## 7.3 Analiza wyników testów wydajnościowych (Kategoria U – Aktualizacja)
**Wnioski z wykresów (`wykres_U.png`):**
Aktualizowanie pojedynczych rekordów, takich jak inkrementacja zmiennej (U1), wypada znakomicie w rozwiązaniach NoSQL. **Redis** (z poleceniem `HINCRBY`) i **MongoDB** (z operatorem `$inc`) rozwiązują ten problem błyskawicznie.
Jednakże przy masowych aktualizacjach warunkowych (np. opartych na podzapytaniach w U5 lub na wielowarunkowych aktualizacjach używających operatora `CASE WHEN` w U6), relacyjne silniki bezbłędnie pokazują swoją przewagę. Wykresy "Z indeksami" potrafią ukazać zauważalne przyspieszenie dla operacji typu (U3), gdzie wskazane indeksy pomagają silnikowi bazy danych błyskawicznie zlokalizować wiersze przeznaczone do aktualizacji, minimalizując tzw. *Table Scan*.

## 7.4 Analiza wyników testów wydajnościowych (Kategoria D – Usuwanie)
**Wnioski z wykresów (`wykres_D.png`):**
Usuwanie płytkie, oparte na znajomości dokładnego klucza (D1), wykonuje się natychmiastowo we wszystkich czterech bazach. W bazach relacyjnych złożone usunięcia kaskadowe lub usuwanie na podstawie złączeń podzapytań (D4) są realizowane pewnie i bez utraty spójności referencyjnej, choć dla gigantycznych porcji danych standardowa instrukcja `DELETE` ulega spowolnieniu ze względu na mechanizmy zabezpieczające transakcje (np. logi WAL w PostgreSQL). Ekstremalny scenariusz czyszczenia bazy (D6) uwidacznia siłę instrukcji DDL typu `TRUNCATE` w bazach SQL, która fizycznie zwalnia obszar danych zwalniając nas z analizy wiersz po wierszu, dzięki czemu operacja jest tak samo natychmiastowa jak zrzucenie kolekcji (`drop()`) w środowisku MongoDB.

## 8. Wnioski 
Zaprojektowany system rzetelnie odwzorował wady i zalety różnych koncepcji badanych SZBD: 
* Praca w chmurze dokumentowej jest obłędnie opłacalna i elastyczna do szybkiego modyfikowania na bieżąco struktur logiki aplikacji i przechowywania dużych płaszczyzn JSONów, dopóty po miesiącu użytkowania developer nie natrafi na konieczność dołączenia z potężnej odrębnej kolekcji np. setek rzędów specyficznej zmiennej przez operacje asocjacji/join, a co za tym idzie naruszy logikę ich szybkiego wstrzykiwania do klienta.
* Bazy Relacyjne to serca bankowości wymagające nakładów programistycznych na początkach projektów, ale stawiające absolutne rygorystyczne wymagania typologiczne i integralnościowe weryfikując nieszczelności i braki obiektowe z logiki systemów - opłacają się w długim torze analiz badawczych i w systemach transakcyjnych. 
* Wprowadzenie indeksów wydajnościowych B-Tree dla badanej aplikacji badającej gigantyczne wolumeny rzędu ponad 1-10 milionów w testowanym systemie MMORPG wykazało drastyczną wymagalność i znaczenie ich istnienia na etapie odczytu statystyk, zmniejszając koszty w środowiskach z rzędu setek tysięcy czasów procesora o 98-99%. 

**Raport wykonany w oparciu na test aplikacyjny i pomiary autorskim systemem wizualizacyjnym na zaliczenie laboratorium z przedmiotu ZTBPD.**
