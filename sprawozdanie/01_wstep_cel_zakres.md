\section{Wstęp}

% Ocena 3.0 (pkt 1): Jasno określony temat i zakres analiz.
\subsection{Cel i zakres pracy}
Głównym celem niniejszego projektu jest przeprowadzenie zaawansowanej, wielobszarowej analizy i porównania wydajności operacji CRUD w czterech wiodących systemach zarządzania bazami danych (SZBD) o odmiennych architekturach: relacyjnych (PostgreSQL, MySQL) oraz nierelacyjnych z rodziny NoSQL (MongoDB, Redis). Analiza ma na celu zbadanie zachowania tych systemów w różnych warunkach obciążeniowych, przy zróżnicowanych wolumenach danych (od dziesiątek tysięcy do milionów rekordów) oraz przed i po zastosowaniu struktur optymalizacyjnych (indeksów).

W ramach realizacji projektu określono następujący zakres prac analitycznych i implementacyjnych:
\begin{itemize}
    \item \textbf{Zaprojektowanie modelu danych:} Przygotowanie złożonego środowiska testowego, składającego się z 12 powiązanych encji osadzonych w logice systemów gier wideo (np. gracze, przedmioty, logi z serwerów).
    \item \textbf{Implementacja w odmiennych architekturach:} Przeniesienie spójnej struktury danych do klasycznego modelu relacyjnego (PostgreSQL, MySQL) oraz do modeli nierelacyjnych: dokumentowego (MongoDB) i klucz-wartość (Redis).
    \item \textbf{Generacja danych obciążeniowych:} Opracowanie mechanizmów zasilających bazy syntetycznymi danymi w trzech skalach wolumenowych: małej (10~000 rekordów), średniej (100~000 rekordów) i dużej (rzędu milionów rekordów).
    \item \textbf{Wykonanie zautomatyzowanych benchmarków:} Przeprowadzenie zautomatyzowanych testów obejmujących 24 unikalne scenariusze CRUD. Scenariusze te sprawdzają wydajność m.in. operacji masowych (\textit{bulk insert}), skomplikowanych złączeń, zapytań agregujących oraz sortowania.
    \item \textbf{Optymalizacja i analiza planów zapytań:} Zbadanie mechanizmów działania silników (przy użyciu komendy \texttt{EXPLAIN}) oraz ocena wpływu specjalistycznych indeksów (np. B-Tree) na szybkość przetwarzania danych.
    \item \textbf{Wizualizacja wyników:} Zebranie, uśrednienie (z trzech niezależnych prób) i graficzna wizualizacja uzyskanych czasów wykonania w podziale na systemy, operacje oraz wielkości zbiorów danych.
\end{itemize}

% Ocena 5.0: Sformułowanie jednej hipotezy badawczej.
\subsection{Hipoteza badawcza}
Na podstawie wstępnej analizy architektur badanych systemów bazodanowych, w ramach projektu sformułowano i poddano weryfikacji następującą hipotezę badawczą:

\textit{H1: Systemy nierelacyjne (MongoDB, Redis) charakteryzują się znacznie wyższą wydajnością w prostych, masowych operacjach zapisu (Bulk INSERT) i bezpośrednich odczytach względem systemów relacyjnych (PostgreSQL, MySQL). Z kolei dla złożonych operacji odczytu (wymagających wielokrotnych złączeń i agregacji), relacyjne systemy z zastosowaniem odpowiednich indeksów wykazują mniejszą degradację wydajności wraz ze wzrostem wolumenu danych, jednakże odbywa się to kosztem zauważalnie dłuższego czasu wykonywania późniejszych operacji modyfikujących zbiór (INSERT, UPDATE).}
