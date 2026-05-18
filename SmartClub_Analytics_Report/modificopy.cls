\LoadClass[a4paper,12pt]{report}

%--------------------- Packages ------------------------

\RequirePackage{titlesec}
\RequirePackage{tocloft}
\RequirePackage[french]{babel}
\RequirePackage[utf8]{inputenc}
\RequirePackage[section]{placeins}
\RequirePackage[T1]{fontenc}
\RequirePackage{mathtools}
\RequirePackage{siunitx}
\RequirePackage{float}
\RequirePackage{graphicx}
\RequirePackage[justification=centering]{caption}
\RequirePackage{subcaption}
\RequirePackage{wallpaper}
\RequirePackage{nomencl}
\RequirePackage{fancyhdr}
\RequirePackage{fancybox}
\RequirePackage{url}
\RequirePackage[hidelinks]{hyperref}
\RequirePackage[left=2.5cm,right=2.5cm,top=2cm,bottom=3.5cm]{geometry}

% Packages for diagrams and code
\RequirePackage{tikz}
\usetikzlibrary{shapes.geometric,shapes.symbols,shapes.multipart,
                arrows.meta,positioning,fit,
                backgrounds,calc,decorations.pathreplacing,decorations.markings,
                shadows.blur,patterns}
\RequirePackage{listings}
\RequirePackage{xcolor}
\RequirePackage{array}
\RequirePackage{booktabs}
\RequirePackage{multirow}
\RequirePackage{enumitem}
\RequirePackage{longtable}

% Colors for code listings
\definecolor{codegreen}{rgb}{0.0,0.5,0.0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0.0,0.82}
\definecolor{backcolour}{rgb}{0.96,0.96,0.94}

% Python language definition for listings
\lstdefinelanguage{PythonExtended}{
  keywords={import, from, class, def, return, if, else, elif, for, while, try,
            except, finally, with, as, pass, break, continue, and, or, not,
            in, is, lambda, yield, async, await, True, False, None, self,
            raise, global, nonlocal, assert, del},
  keywordstyle=\color{blue!80!black}\bfseries,
  ndkeywords={print, len, range, zip, map, filter, sorted, enumerate,
              str, int, float, list, dict, tuple, set, bool, object,
              isinstance, hasattr, getattr, setattr, super, type, open,
              HttpResponse, JsonResponse, Response, APIView, ViewSet,
              ModelViewSet, Serializer, ModelSerializer, ListCreateAPIView,
              RetrieveUpdateDestroyAPIView, Authentication, Permission,
              IsAuthenticated, AllowAny},
  ndkeywordstyle=\color{teal!70!black}\bfseries,
  sensitive=true,
  comment=[l]{\#},
  morecomment=[s]{'''}{'''},
  morecomment=[s]{"""}{"""},
  commentstyle=\color{codegreen}\itshape,
  stringstyle=\color{codepurple},
  morestring=[b]',
  morestring=[b]",
}

\lstdefinestyle{smartclubstyle}{
    backgroundcolor=\color{backcolour},
    commentstyle=\color{codegreen},
    keywordstyle=\color{blue!80!black}\bfseries,
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,
    breaklines=true,
    captionpos=b,
    keepspaces=true,
    numbers=left,
    numbersep=5pt,
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    tabsize=4,
    frame=single,
    rulecolor=\color{black!30}
}
\lstset{style=smartclubstyle}

% Chapter title formatting with frame
\titleformat{\chapter}[frame]
  {\Large}{\filright\enspace \MakeUppercase{\chaptertitlename } \thechapter\enspace}
  {8pt}{\LARGE\bfseries\filcenter}
\titlespacing*{\chapter}{0pt}{-50pt}{40pt}

% Custom commands for report info
\newcommand{\UE}[1]{\renewcommand{\UE}{#1}}
\newcommand{\sujet}[1]{\renewcommand{\sujet}{#1}}
\newcommand{\titre}[1]{\renewcommand{\titre}{#1}}
\newcommand{\enseignant}[1]{\renewcommand{\enseignant}{#1}}
\newcommand{\eleves}[1]{\renewcommand{\eleves}{#1}}

\newcommand{\fairemarges}{
    \fancyhf{}
    \fancyheadoffset{1cm}
    \setlength{\headheight}{1.5cm}
    \fancyfoot[C]{\thepage}
    \renewcommand{\headrulewidth}{1pt}
    \renewcommand{\footrulewidth}{1pt}
    \fancyfoot[L]{SmartClub Analytics}
    \fancyfoot[R]{2024--2025}
    \fancyhead[L]{\nouppercase{\leftmark}}
    \fancyhead[R]{}
    \pagestyle{fancy}
}

\newcommand{\fairepagedegarde}{
\begin{titlepage}

\ThisLRCornerWallPaper{1}{logos/background.jpg}
	
    \centering
    \includegraphics[width=0.3\textwidth]{logos/tekup_logo.png}\par\vspace{1cm}
    {\scshape\LARGE École Supérieure Privée de Technologie et d'Ingénierie \\ TEK-UP \par}
    \vspace{1.5cm}
    {\scshape\Large \UE \\ \sujet \par}
    \vspace{1cm}
    \rule{\linewidth}{0.2 mm} \\ \vspace{0.4cm}
    {\huge\bfseries \titre \\}
    \rule{\linewidth}{0.2 mm} \\ \vspace{1.5cm}
    \vspace{1cm}
    
    \begin{minipage}{0.5\textwidth}
        \begin{flushleft} \large
        \textbf{Élèves :}\\
        \eleves\\
        \end{flushleft}
    \end{minipage}
    ~
    \begin{minipage}{0.4\textwidth}
        \begin{flushright} \large
        \textbf{Encadrant :} \\
        \enseignant \\
        \end{flushright}
    \end{minipage}
    ~
    
    \vfill
    {\large Année Universitaire 2024--2025\par}

\end{titlepage}
}

\newcommand{\tabledematieres}{
\tableofcontents
\newpage
}
