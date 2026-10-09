# Manuscript preamble

The shared template renderer consumes this fenced LaTeX preamble. Layout values
are injected from the validated publication profile.

```latex
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{amsthm}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{graphicx}
\usepackage{float}
\usepackage[section]{placeins}
\floatplacement{figure}{p}
\usepackage{listings}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{fontspec}
\setmonofont{lmmono10-regular.otf}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{remark}[theorem]{Remark}
\newtheorem{example}[theorem]{Example}
\newtheorem{definition}[theorem]{Definition}
\setcounter{tocdepth}{2}
\setcounter{secnumdepth}{3}
\hypersetup{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}
\renewcommand{\bibsection}{}
```
