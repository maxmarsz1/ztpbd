% --------------------------------------------------------------------
% 3. MODELOWANIE I ZBIÓR DANYCH
% --------------------------------------------------------------------
\section{Modelowanie i zbiór danych}

\subsection{Opis modeli danych}
W ramach prowadzonych analiz zaprojektowano uniwersalny, zróżnicowany model danych, odzwierciedlający złożoną logikę wewnętrzną typową dla silników gier wideo (w szczególności z gatunku MMORPG). System ten zakłada współistnienie zasobów takich jak postacie neutralne (NPC), warianty przeciwników, zaawansowane statystyki, przedmioty oraz przepisy rzemieślnicze (\textit{crafting}).

\subsubsection*{Model relacyjny (PostgreSQL, MySQL)}
Architektura w systemach SQL (PostgreSQL, MySQL) oparta jest na klasycznym, silnie znormalizowanym podejściu. Model wykorzystuje łącznie 12 spójnie powiązanych ze sobą tabel za pomocą kluczy głównych (Primary Key) oraz obcych (Foreign Key):

\begin{enumerate}
    \item \textbf{Environments:} Słownik środowisk i biomów w grze (pola: \texttt{id}, \texttt{name}, \texttt{description}).
    \item \textbf{AITypes:} Logika behawioralna oraz typy sztucznej inteligencji jednostek (pola: \texttt{id}, \texttt{name}, \texttt{description}).
    \item \textbf{NPCs:} Główna tabela encji określająca postacie neutralne lub przeciwników, powiązana relacyjnie z mechaniką sztucznej inteligencji (pola: \texttt{id}, \texttt{typeID} -- FK do \texttt{AITypes}).
    \item \textbf{NPCEnvironments:} Tabela asocjacyjna realizująca relację wiele do wielu (N:M) przypisująca konkretne NPC do zdefiniowanych obszarów środowiskowych (pola: \texttt{id}, \texttt{npcID}, \texttt{environmentID}).
    \item \textbf{EnemyVariants:} Poszerzona tabela szczegółowa definiująca warianty i mutacje konkretnych przeciwników (pola: \texttt{id}, \texttt{npcID}, \texttt{AITypeID}, \texttt{type}, \texttt{mode}).
    \item \textbf{EnemyVariantStats:} Tabela przechowująca bojowe i ekonomiczne atrybuty dla danych wariantów przeciwników, odseparowana w celu lepszej czytelności (pola: \texttt{id}, \texttt{variantID}, \texttt{health}, \texttt{damage}, \texttt{defense}, \texttt{coins}).
    \item \textbf{NPCSounds:} Tabela przechowująca odnośniki do zasobów dźwiękowych powiązanych z poszczególnymi postaciami (pola: \texttt{id}, \texttt{npcID}, \texttt{url}).
    \item \textbf{Stats:} Tabela zawierająca zaawansowane modyfikatory sprzętu zapisane w elastycznym formacie tekstowym/obiektowym (pola: \texttt{id}, \texttt{itemID}, \texttt{data} -- np. typu \texttt{JSONB} przetrzymujące pary klucz-wartość dla parametrów takich jak obrażenia czy obrona).
    \item \textbf{Items:} Główna tabela encji definiująca przedmioty w grze (ekwipunek, bronie, materiały). Posiada bezpośrednie odniesienia do statystyk (pola: \texttt{id}, \texttt{name}, \texttt{description}, \texttt{type}, \texttt{material}, \texttt{statsID}, \texttt{sellPrice}).
    \item \textbf{ItemsRecipies:} Struktura nagłówkowa definiująca schematy tworzenia (rzemiosła) oraz stacje robocze wymagane do danego przepisu (pola: \texttt{id}, \texttt{itemID}, \texttt{craftingStation}).
    \item \textbf{Recipies:} Tabela asocjacyjna agregująca konkretne przedmioty (materiały składowe) przypisane do danego schematu tworzenia (pola: \texttt{id}, \texttt{itemRecipieID}, \texttt{itemID}, \texttt{amount}).
    \item \textbf{EnemyDrops:} Określa pule nagród (\textit{loot tables}) oraz prawdopodobieństwo ich wystąpienia po pokonaniu danego wariantu przeciwnika (pola: \texttt{id}, \texttt{variantID}, \texttt{itemID}, \texttt{rate}).
\end{enumerate}

\begin{figure}
    \centering
    % Odkomentuj i dostosuj ścieżkę do wygenerowanego pliku ze schematem ERD
    \includegraphics[width=\textwidth]{erd.png}
    \caption{Diagram związków encji (ERD) zaprojektowanego relacyjnego modelu danych}
    \label{fig:erd_diagram}
\end{figure}

\subsubsection*{Model nierelacyjny: Dokumentowy (MongoDB) i Klucz-Wartość (Redis)}
W przypadku bazy \textbf{MongoDB}, wysoce znormalizowany model relacyjny został zdenormalizowany i przekształcony w formę zagnieżdżonych dokumentów JSON/BSON. Zamiast dzielić encje na wiele małych tabel, zastosowano agregację powiązanych informacji. Przykładowa uproszczona struktura dokumentu przeciwnika z wbudowanymi statystykami i szansami na łupy prezentuje się następująco:
\begin{verbatim}
{
  "_id": ObjectId("..."),
  "typeID": 1,
  "variant": {
    "type": "Mutant",
    "mode": "Hard",
    "stats": { "health": 1500, "damage": 45, "defense": 12, "coins": 500 },
    "drops": [ { "itemID": 12, "rate": 0.05 }, { "itemID": 45, "rate": 0.25 } ]
  }
}
\end{verbatim}
Taka konstrukcja omija problem kosztownych złączeń (JOIN), dostarczając kompletny obiekt biznesowy w jednej prostej operacji odczytu.

W bazie \textbf{Redis} model zaimplementowano stosując struktury typu \texttt{HASH}. Relacyjne rekordy zostały spłaszczone do postaci par klucz-wartość, gdzie kluczem jest unikalny identyfikator (np. \texttt{Items:1255}), a wartością zestaw atrybutów danej encji.

\subsection{Charakterystyka zbioru danych}
Zbiór danych wygenerowany na potrzeby testów benchmarkowych oparty jest na mechanizmach biblioteki \texttt{Faker} (język Python), dzięki czemu symuluje zróżnicowane i zbliżone do naturalnych dane aplikacji z dużą losowością cech.
\begin{itemize}
    \item \textbf{Typy pól:} Modele wykorzystują różnorodne typy danych: identyfikatory numeryczne (\texttt{INT}, \texttt{BIGINT}), ciągi znaków dla nazw, opisów oraz adresów URL (\texttt{VARCHAR}, \texttt{TEXT}), a także liczby zmiennoprzecinkowe (\texttt{FLOAT}, \texttt{DOUBLE}) dla wskaźników szans (\textit{rate}) i zaawansowanych statystyk.
    \item \textbf{Relacyjność:} Zbiór obfituje w gęstą sieć połączeń. Przedmioty łączą się ze statystykami i przepisami tworzenia (relacja 1:N z dodatkową tabelą asocjacyjną N:M dla składników). Przeciwnicy posiadają rozbudowane relacje z łupami oraz typami środowisk.
    \item \textbf{Wolumeny danych:} System wspiera wprowadzanie profili objętościowych w trzech skalach:
    \begin{itemize}
        \item \textbf{Mały profil ($\sim$10~000 rekordów):} Służący za szybki punkt odniesienia (środowisko deweloperskie).
        \item \textbf{Średni profil ($\sim$100~000 rekordów):} Standardowy profil do ukazywania przewagi architektury relacyjnej i dokumentowej w zadaniach operacyjnych.
        \item \textbf{Duży profil ($\sim$10~000~000 rekordów):} Masowy zbiór stworzony do mierzenia czasu skomplikowanych złączeń, wpływu indeksowania na ogromne wolumeny oraz zachowania systemów w testach tzw. \textit{Bulk Insert} i \textit{Update}.
    \end{itemize}
\end{itemize}

% --------------------------------------------------------------------
% 4. ŚRODOWISKO BADAWCZE I APLIKACJA TESTOWA
% --------------------------------------------------------------------
\section{Środowisko badawcze i aplikacja testowa}

\subsection{Architektura aplikacji testowej}
Zaprojektowane środowisko badawcze stanowi spójny, wysoce zautomatyzowany ekosystem stworzony na potrzeby obiektywnych pomiarów wydajności baz danych.

\begin{itemize}
    \item \textbf{Wymagania i technologie systemowe:} Jądro platformy testowej zostało zaimplementowane w języku Python w wersji 3.11. Wszystkie cztery badane systemy zarządzania bazami danych (PostgreSQL, MySQL, MongoDB, Redis) zostały całkowicie skonteneryzowane i zainicjowane za pomocą technologii Docker i Docker Compose, co gwarantuje pełną izolację zasobów i powtarzalność środowiska testowego na różnych maszynach lokalnych.
    \item \textbf{Integracja (Sterowniki):} W warstwie pośredniczącej aplikacja komunikuje się bezpośrednio z poszczególnymi portami silników z wykorzystaniem natywnych, najbardziej zoptymalizowanych bibliotek-sterowników: \texttt{psycopg2} (dla PostgreSQL), \texttt{mysql-connector-python} (dla MySQL), \texttt{pymongo} (dla MongoDB) oraz dedykowanego pakietu \texttt{redis}.
    \item \textbf{Narzędzia mierzenia czasu:} W celu analizy surowego czasu egzekucji poleceń w bazach aplikacja wykorzystuje wbudowany moduł \texttt{time} (metoda \texttt{time.time()}). Aby uniknąć całkowitego zablokowania środowiska przez wysoce niewydajne zapytania (szczególnie symulacje złączeń JOIN w MongoDB na masowych zbiorach), zaprojektowano własny mechanizm limitowania czasu wykonywania algorytmu z zastosowaniem puli wątków (\texttt{concurrent.futures.ThreadPoolExecutor}). Wymusza on ograniczenie maksymalnego czasu wykonania do 120 sekund, po przekroczeniu którego transakcja jest oznaczana komunikatem "TIMEOUT".
    \item \textbf{Zasada działania operacyjnego:} Badanie zostało podzielone na dwie zasadnicze fazy. Skrypt uruchamia pełen cykl zapytań na tabelach pozbawionych optymalizacji, by ocenić ich podstawową sprawność, a w fazie drugiej dynamicznie aplikuje zestaw zadeklarowanych indeksów pomocniczych (np. na pola \texttt{typeID}, \texttt{sellPrice}, \texttt{statsID} i wewnątrz zagnieżdżonego pola optymalizacyjnego \texttt{JSONB}) i ponownie ewaluuje szybkość 24 scenariuszy testowych dla ukazania narzutu i korzyści płynących z odpowiedniego użycia wskaźników. Pomiędzy fazami dodano 10-sekundowe przerwy na zrzucenie buforów z pamięci RAM do dysku, w celu wykluczenia zakłamań z tytułu działania pamięci podręcznej.
\end{itemize}


\subsection{Automatyzacja procesu testowania}
Rdzeń badawczy został wykreowany z myślą o pełnej autonomii dla zminimalizowania błędów ręcznego wywoływania zapytań i przerw infrastrukturalnych.

\begin{enumerate}
    \item \textbf{Inicjacja i zestawienie sesji:} Po starcie aplikacja samoczynnie nasłuchuje portów wszystkich silników i weryfikuje ich gotowość przy pomocy funkcji oczekiwania. Po poprawnym uwierzytelnieniu, z każdą instancją bazy nawiązywana jest nieprzerwana sesja z przygotowanym zestawem kursorów.
    \item \textbf{Iteracja i sekwencyjność zapytań:} Aplikacja sekwencyjnie wykonuje ustandaryzowaną serię instrukcji z puli w klasyfikacji CRUD. Dla wyeliminowania błędu sprzętowego (np. wahań i losowych opóźnień systemu gospodarza), \textbf{każde zapytanie wywoływane jest trzykrotnie ($N=3$)}. Skrypt po drodze weryfikuje ewentualne niepowodzenia transakcji (odpalając zabezpieczające \texttt{ROLLBACK} w SQL) i generuje czysty wynik liczbowy będący matematyczną średnią arytmetyczną pomiarów czasowych.
    \item \textbf{Zapis wyników do raportu:} Oprócz weryfikacji samej prędkości zapisu i odczytu, mechanizm wymusza wyciągnięcie natywnych planów zapytań przez polecenie \texttt{EXPLAIN}. Plany te są gromadzone globalnie i na końcu funkcjonowania obiektu rzutowane bezpośrednio do fizycznego, wnikliwego pliku diagnostycznego \texttt{benchmark\_explain\_[profil].txt}. Zagregowane zaś wartości uśrednionych pomiarów czasowych transakcji ze wszystkich 4 silników w formie zagnieżdżonych struktur aplikacji serializują się do uniwersalnego formatu z rozszerzeniem \texttt{.json} (raport \texttt{benchmark\_results\_[profil].json}).
    \item \textbf{Wykorzystanie wyjścia:} Wygenerowany strukturalny dokument JSON jest następnie odczytywany w odizolowanym module analitycznym (np. \texttt{plot\_results.py}). Moduł ten dokonuje obróbki i parsowania danych i posługuje się funkcjami nakładki \texttt{Matplotlib} w celu ostatecznego naszkicowania precyzyjnych i wizualnie przystępnych wykresów prezentujących wady i zalety architektoniczne silników bazodanowych na tle konkretnego zestawu warunków objętościowych i strukturalnych.
\end{enumerate}
% --------------------------------------------------------------------
% 5. METODOLOGIA BADAŃ TESTOWYCH
% --------------------------------------------------------------------
\section{Metodologia badań testowych}

\subsection{Scenariusze i procedury testowe}
Na potrzeby ewaluacji silników bazodanowych zaprojektowano zestaw 24 zróżnicowanych scenariuszy testowych, po 6 dla każdej z głównych operacji klasy CRUD (Create, Read, Update, Delete). Zostały one dobrane w taki sposób, aby przetestować systemy zarówno w prostych obciążeniach, jak i w złożonych zadaniach obliczeniowych i analitycznych.

\begin{itemize}
    \item \textbf{Operacje zapisu (INSERT):}
    \begin{enumerate}
        \item \textit{Single Insert:} Wstawienie pojedynczego rekordu ze standardowymi atrybutami.
        \item \textit{Batch Insert (10):} Wstawienie paczki 10 rekordów w jednej transakcji.
        \item \textit{Bulk Insert (1000):} Masowe operacje wstawiania 1000 rekordów (np. polecenia \texttt{execute\_values} lub \texttt{insert\_many}).
        \item \textit{Dependent Insert:} Równoległe wstawianie powiązanych ze sobą rekordów, weryfikujące narzuty na więzy spójności (klucze obce).
        \item \textit{Upsert:} Operacja typu "wstaw lub aktualizuj" (tzw. \texttt{ON CONFLICT DO UPDATE}).
        \item \textit{Deep Nested Insert:} Tworzenie zagnieżdżonego drzewa powiązań (zapis do 3-4 tabel jednocześnie lub głębokie zagnieżdżenie dokumentu w wierszu JSON).
    \end{enumerate}
    
    \item \textbf{Operacje odczytu (SELECT):}
    \begin{enumerate}
        \item \textit{Read By PK:} Pobranie pojedynczego rekordu na podstawie jego unikalnego klucza głównego.
        \item \textit{Read Filter Simple:} Standardowe, liniowe filtrowanie zbioru (operator matematyczny $>$) wraz z limitem wierszy.
        \item \textit{Read Filter Range:} Filtrowanie po zakresie (\texttt{BETWEEN}) z dodatkowym skanowaniem w głąb obiektu (np. wyciąganie wartości z pola \texttt{JSONB}).
        \item \textit{Aggregate Count:} Przeszukiwanie całej tabeli, grupowanie wyników (\texttt{GROUP BY}) i zliczanie ich wystąpień (\texttt{COUNT}).
        \item \textit{Join Small:} Proste łączenie strukturalne dwóch dużych tabel relacyjnych (\texttt{JOIN}).
        \item \textit{Complex Query:} Analityczne zapytanie wymagające trzykrotnego złączenia tabel, wbudowanej agregacji matematycznej (\texttt{AVG}), grupowania i restrykcyjnego sortowania po uśrednionej wartości (\texttt{ORDER BY AVG() DESC}).
    \end{enumerate}
    
    \item \textbf{Operacje modyfikacji (UPDATE):}
    \begin{enumerate}
        \item \textit{Update Single:} Aktualizacja wybranego parametru konkretnego rekordu po kluczu głównym.
        \item \textit{Update Math:} Masowa aktualizacja w oparciu o prostą operację matematyczną (inkrementację o 1) aplikowaną na atrybut wyłuskany z zagnieżdżonego pola \texttt{JSONB}.
        \item \textit{Update In Condition:} Skoncentrowana zmiana atrybutu (negacja flagi boolean) wykorzystująca operator \texttt{IN ()}.
        \item \textit{Replace Full:} Całkowite nadpisanie atrybutów opisowych rekordu (tzw. operacja wstrzyknięcia całego obiektu).
        \item \textit{Update With Subquery:} Aktualizacja danych na podstawie wstrzykniętego podzapytania (skanowanie innej struktury dla odnalezienia id do aktualizacji).
        \item \textit{Bulk Case-When Update:} Warunkowa, masowa operacja aktualizacji logiki oparta na instrukcji rozwidlenia \texttt{CASE WHEN}.
    \end{enumerate}
    
    \item \textbf{Operacje usuwania (DELETE):}
    \begin{enumerate}
        \item \textit{Delete Single:} Bezpośrednie usunięcie pojedynczego rekordu wskazanego kluczem.
        \item \textit{Delete By Condition:} Zeskanowanie tabeli i usunięcie dziesiątek rekordów spełniających dany warunek (operator $> $).
        \item \textit{Delete Range:} Usuwanie zwartych pakietów na podstawie przedziału \texttt{BETWEEN}.
        \item \textit{Delete Subquery:} Kaskadowe wycinanie rekordów odnalezionych przez zapytanie wybierające dane z innych powiązanych tabel.
        \item \textit{Delete Batched:} Kontrolowane ograniczanie bazy dążące do wycięcia zadanej liczby wierszy (klauzula \texttt{LIMIT}).
        \item \textit{Delete All (Truncate):} Agresywne zrzucanie struktury danych, natychmiastowe czyszczenie tabeli (\texttt{TRUNCATE} z ominięciem testów spójności kaskadowej).
    \end{enumerate}
\end{itemize}

\subsubsection*{Wolumeny danych i standaryzacja prób}
W celu zbadania zachowań silników pod diametralnie różnym obciążeniem, eksperymenty przeprowadzono dla trzech wygenerowanych zestawów (profili) danych. Rekordy zostały wstrzyknięte z wykorzystaniem zdefiniowanych mnożników objętości, aplikowanych na bazową pulę ok. 16~milionów encji:
\begin{itemize}
    \item \textbf{Mały zbiór danych (profil \texttt{maly}):} Łącznie ok. 160~000 wygenerowanych rekordów we wszystkich tabelach (mnożnik 0.01). Służy do analizy podstawowego narzutu silnika na parsowanie zapytań i operacje jednostkowe w dogodnych warunkach całkowitego buforowania w szybkiej pamięci RAM (cache).
    \item \textbf{Średni zbiór danych (profil \texttt{sredni}):} Łącznie ok. 1~600~000 rekordów (mnożnik 0.10). Zaczyna wywierać zauważalną presję na operacje wielotabelowe i uwidacznia różnice pomiędzy sekwencyjnym skanowaniem dysku a użyciem wskaźników pamięci oraz logiką indeksowania dla kilkuset tysięcy powiązań (np. w obrębie złączeń \texttt{Items} i \texttt{Stats}).
    \item \textbf{Duży zbiór danych (profil \texttt{duzy}):} Zbiór wymierzony celowo w pułap ok. 10~000~000 rekordów w całej architekturze bazy (osiągnięte mnożnikiem 0.62 względem bazy 16M). Stanowi on niezwykle agresywny wolumen wyczerpujący limity sprzętowe. Profil ten doskonale uwydatnia skalowalność poziomą oraz pionową poszczególnych architektur bazodanowych, co prowadzi do drastycznego rozwarstwienia wydajności m.in. w trakcie skomplikowanych złączeń (JOIN) czy skokowego zjawiska opóźnień podczas modyfikowania wielowarstwowych drzew indeksów B-Tree.
\end{itemize}

Dla zachowania pełnej obiektywności, uniezależnienia od fluktuacji zasobów systemowych gospodarza (tzw. mikro-przycięć procesora, I/O dysku czy interwencji \textit{Garbage Collectora} w aplikacji bazowej), wprowadzono \textbf{zasadę trzykrotnej próby eksperymentalnej ($N=3$)}. Aplikacja w głównej pętli powtarza to samo żądanie bazodanowe trzy razy z rzędu na tej samej bazie. Skrypt rejestruje czas wykonania każdej pojedynczej operacji, sumuje wynik i dzieli przez liczbę podjętych prób. Ostateczną daną wejściową przesyłaną do modułu tworzącego raporty statystyczne jest uśredniona wartość arytmetyczna z tego cyklu, zapewniająca wysoką wierność i rzetelność empiryczną analizy.
