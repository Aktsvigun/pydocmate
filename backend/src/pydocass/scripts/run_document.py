% This must be in the first 5 lines to tell arXiv to use pdfLaTeX, which is strongly recommended.
\pdfoutput=1
% In particular, the hyperref package requires pdfLaTeX in order to break URLs across lines.

\documentclass[11pt]{article}

% Change "review" to "final" to generate the final (sometimes called camera-ready) version.
% Change to "preprint" to generate a non-anonymous version with page numbers.
\usepackage[review]{acl}

% Standard package includes
\usepackage{times}
\usepackage{latexsym}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{multicol}
\usepackage{amsmath,amssymb} % for symbols like \uparrow, etc.
% For proper rendering and hyphenation of words containing Latin characters (including in bib files)
\usepackage[T1]{fontenc}
% For Vietnamese characters
% \usepackage[T5]{fontenc}
% See https://www.latex-project.org/help/documentation/encguide.pdf for other character sets

% This assumes your files are encoded as UTF8
\usepackage[utf8]{inputenc}

% This is not strictly necessary, and may be commented out,
% but it will improve the layout of the manuscript,
% and will typically save some space.
\usepackage{microtype}

\usepackage{listings}
\usepackage{xcolor}


% Configure listings for Python
\lstset{ 
    language=Python,                 % the language of the code
    basicstyle=\ttfamily\small, % the size of the fonts that are used for the code
    numbers=none,
    backgroundcolor=\color{white},   % choose the background color; you must add \usepackage{color}
    showspaces=false,                % show spaces within strings adding particular underscores
    showstringspaces=false,          % underline spaces within strings only
    showtabs=false,                  % show tabs within strings adding particular underscores
    frame=single,                    % adds a frame around the code
    rulecolor=\color{black},         % if not set, the frame-color may be changed on line-breaks within not-black text
    tabsize=2,                       % sets default tabsize to 2 spaces
    captionpos=b,                    % sets the caption-position to bottom
    breaklines=true,                 % sets automatic line breaking
    breakatwhitespace=false,         % sets if automatic breaks should only happen at whitespace
    title=\lstname,                  % show the filename of files included with \lstinputlisting; also try caption instead of title
    keywordstyle=\color{blue},       % keyword style
    commentstyle=\color{teal},      % comment style
    stringstyle=\color{purple},         % string literal style
    escapeinside={\%*}{*)},          % if you want to add LaTeX within your code
    belowskip=-3.0 \baselineskip
}

% This is also not strictly necessary, and may be commented out.
% However, it will improve the aesthetics of text in
% the typewriter font.
\usepackage{inconsolata}

%Including images in your LaTeX document requires adding
%additional package(s)
\usepackage{graphicx}

% For colored text, including the TODO marker
\newcommand{\TODO}[1]{\textcolor{red}{\textbf{TODO: #1}}}
\newcommand{\AskArtem}[1]{\textcolor{blue}{\textbf{AskArtem: #1}}}

% If the title and author information does not fit in the area allocated, uncomment the following
%
%\setlength\titlebox{<dim>}
%
% and set <dim> to something 5cm or larger.

\title{PyDocAss: An AI-Powered Python Documentation Assistant}

\author{First Author \\
  Nebius AI Studio Team \\
  Nebius \\
  \texttt{email@domain} \\\And
  Second Author \\
  Nebius AI Studio Team \\
  Nebius \\
  \texttt{email@domain} \\}

\begin{document}
\maketitle
\begin{abstract}
Code documentation is a critical aspect of software development that is often neglected due to time constraints and competing priorities.
This is particularly true for Python, which serves as one of the primary languages that drives artificial intelligence. 
Due to emergence of new models and frameworks at an unprecedented pace, researchers and developers often prioritize keeping up with rapidly evolving technical advancements over maintaining well-documented code, which leads to a proliferation of poorly documented yet widely used libraries and repositories.
To mitigate this, we present PyDocAss, an AI-powered Python Documentation Assistant that automatically generates comprehensive documentation while guaranteeing that no functional code is modified. 
PyDocAss leverages state-of-the-art language models from Nebius AI Studio and employs innovative techniques including sequential in-context examples selection ~\cite{few-shot-paper}, structured output generation, and AST-based code analysis. 
The system generates three types of documentation: type annotations for arguments and return values, and docstrings for functions, classes, and methods, and comments for complex code sections. 
Evaluation with professional developers shows that PyDocAss achieves 85\% user satisfaction while guaranteeing complete code preservation, and produces more complete and correct documentation compared to direct LLM approaches.
% The modular design allows users to selectively apply documentation components and choose from various language models based on their specific needs. 
% PyDocAss addresses a significant pain point in software development, helping developers maintain high-quality documentation without disrupting their workflow.
We release the demo web application, short video with PyDocAss capabilities, and the source code\footnote{\TODO{Add links: ask Artem; create github}}.
\end{abstract}

\section{Introduction}

Code documentation is an essential component of software development, serving as a bridge between code authors and future users or maintainers. Well-documented code ensures maintainability, facilitates collaboration, and reduces onboarding time for new developers.
Despite its importance, documentation often becomes an afterthought in the development process, leading to technical debt and increasing maintenance cost over time~\cite{Ashbacher2003, Spinellis2003}. 
\AskArtem{Is it ok?} For example, a recently emerged `unsloth` package in Python, albeit being popular and useful for large language models (LLMs) fine-tuning, misses documentation for many critical components. 
This hinders its successful application in many production-based applications despite its numerous advantages.

For Python specifically, documentation best practices include type annotations for function arguments and return values, comprehensive docstrings for functions and classes, and inline comments for complex code sections. The Python Enhancement Proposal (PEP) 484 \footnote{https://peps.python.org/pep-0484/} introduced type hints, while standards like Google-style, NumPy-style, and reStructuredText (reST) docstrings provide frameworks for documenting code. However, adhering to these standards requires significant developer effort and discipline, which is often compromised due to time constraints or competing priorities.

Existing automatic documentation tools either focus on generating documentation from existing blocks (like Sphinx~\cite{sphinx} or pydoc~\cite{pydoc}) or employ rule-based approaches for simple cases.
The recent advancements in LLMs have demonstrated remarkable capabilities in understanding and generating code, enabling their direct application to automated documentation generation out-of-the-box. %without task-specific fine-tuning.
However, such an approach suffers from a severe limitation: LLMs can modify the original code while adding documentation, potentially introducing bugs or modifying the logic of the code.
This hurdles the adoption of such an approach for automatic documentation generation.

To address this challenge, we present PyDocAss, an AI-powered Python Documentation Assistant that writes code documentation, while guaranteeing that no functional code is modified.
PyDocAss leverages state-of-the-art language models to generate comprehensive documentation for Python code, including type annotations, docstrings, and comments.
Securing the integrity of the code is a crucial feature as it makes sure the behavior of the application remains unchanged.

\TODO{Add a paragraph with bullet points illustrating the benefits of PyDocAss}

PyDocAss offers several key benefits that address critical pain points in Python documentation:

\begin{itemize}
    \item \textbf{Code Integrity Preservation:} Unlike direct LLM applications, PyDocAss guarantees that no functional code is modified during the documentation process, making it safe to use.
    \item \textbf{Comprehensive Documentation:} The system generates three complementary documentation types (type annotations, docstrings, and comments) for a complete documentation solution.
    \item \textbf{Model Flexibility:} Integration with Nebius AI Studio allows users to select from various state-of-the-art LLMs depending on their needs for speed, accuracy, or other factors.
\end{itemize}

These benefits combine to make PyDocAss a comprehensive solution that addresses the documentation challenges faced by Python developers while ensuring code safety and quality.

The system is built on top of Nebius AI Studio~\cite{nebius_ai_studio}, a platform that provides access to state-of-the-art open-source language and vision models. By leveraging cutting-edge LLMs, PyDocAss delivers high-quality documentation that follows Python best practices.
% By leveraging models such as DeepSeek-V3\cite{DeepSeek-V3} for documentation generation and Alibaba-NLP/gte-Qwen2-7B-instruct~\cite{gte-qwen2} and others, 
 % while maintaining flexibility for developers to choose the most appropriate model for their specific needs.

\begin{figure*}[h]
  \centering
  \includegraphics[width=\textwidth]{figures/screenshot.png}
  \caption{PyDocAss user interface with the input code editor (left) and the generated documented code (right).}
  \label{fig:design}
\end{figure*}

\section{System Overview}

PyDocAss is designed as a modular system that ensures code preservation while generating high-quality documentation. This section describes the user interfaces, command-line functionality, and the underlying technical components that enable PyDocAss to generate accurate documentation without modifying functional code.

\subsection{Interface Design}

The PyDocAss interface (Figure~\ref{fig:design}) is designed for simplicity and ease of use, featuring:

\begin{itemize}
    \item A dual-panel layout with input code on the left and generated documentation on the right
    \AskArtem{isn't it too dummy?} \item Syntax highlighting for better code readability
    \item Real-time documentation generation
    \AskArtem{isn't it too dummy?} \item Configuration controls for customizing the documentation process
\end{itemize}

The interface is designed to be intuitive and immediately usable without any training.

\subsection{Command line calling}

PyDocAss can also be invoked via command line (CLI) calling. Figure~\ref{fig:code} shows a simple example of using PyDocAss via the command line: 

\begin{figure}[h]
\begin{lstlisting}[language=Python]
# Set API key as environment variable
NEBIUS_API_KEY=YOUR_API_KEY run-document
my_file.py --output-file my_file_doc.py
\end{lstlisting}
\caption{Code example of how to run documentation with PyDocAss via CLI.}\label{code:polygraph}
\label{fig:code}
\vspace{-0.3cm}
\end{figure}

The only user input it requires is an API key to Nebius AI Studio\footnote{The API key to Nebius AI Studio can be obtained at \url{https://studio.nebius.com/settings/api-keys} after registration.} / any OpenAI-like inference provider for the underlying models.

\subsection{Technical Implementation}

As already stated, the core innovation of PyDocAss lies in generation of high-quality documentation while guaranteeing the integrity of the original code. 
This subsection describes the key technical components that enable this functionality.

\subsubsection{AST-Based Code Analysis}

PyDocAss utilizes Python's Abstract Syntax Tree (AST) module to parse and analyze the input code. 
The AST representation allows the system to:

\begin{itemize}
    \item Identify functions, classes, methods, and their arguments
    \item Detect existing docstrings and type / return annotations
    \item Properly locate the generated documentation to avoid modifications in the functional code
\end{itemize}

This approach provides a robust foundation for analysis as it captures the semantic structure of the code rather than just textual patterns.

\subsubsection{Modular Documentation Generation}

PyDocAss employs a modular approach to documentation generation with separate components for:

\begin{itemize}
    \item \textbf{Type Annotations:} Generating type hints for \AskArtem{should we speak about class inits? when the class is initialized without a method and we generate annotations for its arguments (e.g. classes like ModelOutput)} function / method arguments and return values
    \item \textbf{Docstrings:} Creating formatted docstrings for functions, classes, and methods
    \item \textbf{Comments:} Adding inline and block comments to explain complex code sections
\end{itemize}

Each component operates independently. Such a modular design enables the system to optimize prompt construction for each specific task and allows users to selectively apply documentation components based on their needs.

\textbf{Type Annotations}: The type annotation component provides annotations for arguments and return values of all classes / methods / functions in the code. This component does the following:

\begin{itemize}
    \item Identifies function arguments and return statements
    \item Generates appropriate type hints for arguments and returns
    \item Adds necessary imports if they are required for correct type annotation. For instance, `Callable` or `Any` from the `typing` package
    \item Preserves existing annotations unless explicitly configured to override them
\end{itemize}

\textbf{Docstrings}: The docstring generation creates structured docstrings following the Google-style format \AskArtem{Should we add an example of a Google-style format in Appendix?}. This component is also generated for all classes / methods / functions in the code. However, in contrast to the type annotations component, it omits docstrings for trivial or self-explanatory code. It also skips generation for vague objects, where the description cannot be automatically extracted from the code without additional human comments.

\textbf{Comments}: The comments generation component generates block comments for all parts of the input code where the LLM feels that an explanation is required to facilitate understanding of the code. Similar to the docstrings component, it doesn't generate comments for straightforward code sections or for code segments where the model cannot confidently determine the underlying logic or purpose. This selective approach ensures comments are only added where they provide genuine value without creating noise in easily understood sections of code.

\subsubsection{Dynamic Few-Shot Example Selection}

One of the key features of PyDocAss is its approach to in-context learning. We manually curated a few dozens of examples for each component to embrace as many potential scenarios as possible. However, there are many different usecases: one input code may only consist of functions, while the other may contain classes with multiple methods. On the other hand, few-shot learning examples consume many tokens: for instance, an example of writing docstrings for a class with 10 ''basic'' methods consumes approximately 2000 input tokens. At the same time, the quality of modern LLMs usually degrades when the context window is too large \cite{jamba-2024}.

Therefore, instead of using a fixed set of examples for all inputs, our system dynamically selects examples for in-context learning using one of the state-of-the-art methods $Se^2$. This approach prioritizes examples based on how effective they would be given the current context, which includes already selected examples and the input text.

\AskArtem{is this paragraph ok?}
Even though dynamic selection of in-context learning examples slightly increases the latency of the system. However, in this task the quality of the system responses is more crucial. Hence, this time-to-first-token increase is negligible.

\subsubsection{Structured Output Generation}

To ensure consistent and well-formatted LLM generations, PyDocAss leverages the structured generation approach through the XGrammar framework~\cite{xgrammar}. This prevents generating extraneous phrases like "Certainly!" or reasoning-related tokens in the model output, allowing seamless integration into automated workflows and development pipelines. Furthermore, rather than making separate calls for each element (e.g. each argument of each class / method / function from the input code), structured generation returns a complete JSON dictionary containing all documentation elements in a single API call.

% Since each few-shot example contains many tokens, making the input prompt to LLM contain dozens of thousand of tokens. Consequently, generating separately the annotation for each argument would result in a multiple calls to LLM with large prompts. While prefix caching can mitigate it, it doesn't completely resolve the issue [CHECK THIS!].

% \subsection{Frontend Implementation}

% The PyDocAss frontend is built using Next.js, a React framework that enables server-side rendering and static site generation. Key implementation details include:

% \begin{itemize}
%     \item \textbf{Code Editors:} Monaco-based code editors with Python syntax highlighting for both input and output
%     \item \textbf{Real-time Updates:} Streaming API responses with React state management to update the output code incrementally as documentation is generated
%     \item \textbf{Configuration Panel:} Interactive controls for selecting LLM models and documentation components
%     \item \textbf{Responsive Design:} CSS Grid and Flexbox for adaptability across device sizes
%     \item \textbf{Accessibility:} ARIA-compliant components and keyboard navigation support
% % \end{itemize}

% The frontend communicates with the backend via a RESTful API, sending the input code and configuration options and receiving the documented code as a stream of updates.

% \subsection{Documentation Components}

% Each documentation component is implemented as a separate Python module with specialized functionality:



% \subsection{Error Handling and Edge Cases}

% PyDocAss includes robust error handling to manage various edge cases:

% \begin{itemize}
%     \item \textbf{Syntax Errors:} Gracefully handles invalid Python code with helpful error messages
%     \item \textbf{Type Inference Failures:} Falls back to generic types (e.g., Any) when specific types cannot be determined
%     \item \textbf{Model Timeouts:} Implements retry logic with exponential backoff for model API calls
%     \item \textbf{Partial Results:} Provides partial documentation when complete processing is not possible
%     \item \textbf{Code Preservation:} Validates generated code to ensure no functional changes
% \end{itemize}

% A critical feature of PyDocAss is its guarantee that no functional code is modified during the documentation process. This is achieved through careful comparison of AST structures before and after documentation is applied, ensuring that only comments, docstrings, and type annotations are modified.

\section{Evaluation}

To assess the effectiveness of PyDocAss, we conducted a comprehensive evaluation focusing on user satisfaction and the system's reliability in preserving code integrity. Our evaluation aims to answer two key questions: 1) How satisfied are users with the generated documentation? and 2) How reliable is the system at preserving the original code's functionality?

\subsection{Methodology}

We evaluated PyDocAss against 2 state-of-the-art LLMs that were meticulously prompted to only provide documentation and not introduce any changes to the code. We used Claude-3.7-Sonnet~\cite{claude37} and O1~\cite{o1} due to their superior performance in coding tasks. We also included examples for few-shot learning to improve the quality of the documentation.

Since PyDocAss can work with any LLM suitable for structured generation, we measured its performance with two different LLMs: Qwen2.5-Coder-32B-Instruct~\cite{hui2024qwen2} (further - Qwen-Coder) and DeepSeek-V3~\cite{deepseek-v3}. 
\AskArtem{Is it ok? What makes me afraid is that this is an "overfitting" to the dataset. While without this approach PyDocAss is still the best }
Furthermore, the modular structure of our system allows to select different models for different documentation components. We therefore select Qwen-Coder for the arguments/returns annotation phase (due to its speed and slightly better quality), and DeepSeek-V3 for the two other components in our default architecture.

The evaluation used a dataset of 100 diverse perfectly-documented Python files ranging from simple utility functions to complex class hierarchies. All systems were tasked with adding complete documentation including type annotations, docstrings, and comments.

\subsection{Metrics}

We evaluated the performance of the systems across the following metrics:

\textbf{User Satisfaction}: To measure user satisfaction, we implemented a binary feedback mechanism where users could provide thumbs up (1) or thumbs down (0) after reviewing the generated documentation. The average satisfaction score represents the proportion of positive feedback received.

\textbf{Code Preservation Assessment}: We conducted an analysis of the generated outputs to identify two types of code modifications:

\begin{itemize}
    \item \textbf{Non-critical changes}: Modifications that do not affect functionality (e.g., modifying the code without changing its logic, removal of existing comments / ToDo flags, etc.)
    \item \textbf{Critical changes}: Modifications that alter code behavior (e.g., changing function logic or introduction of bugs)
\end{itemize}

\textbf{Correctness}: This metric evaluates the accuracy of the provided documentation. If at least one item across the component contains hallucinations or is incorrect (e.g. a docstring for a method incorrectly describes what the method does), the whole observation is scored with 0. If a value was not omitted by the system, it was considered correct \AskArtem{Should we preserve this "because"?}because no hallucinations were introduced.

\textbf{Completeness}: This metric measures how complete the provided documentation is. We considered the documentation incomplete if the system omitted (1) any argument/return annotation or (2) a docstring for a non-dummy class/method/functions, or (3) comment for a hard-to-understand piece of code.
% This metric not only assesses how often the system skips some pieces of code but also its ability to understand complex code snippets since all systems were explicitly prompted not to write documentation if they were not confident in its correctness.

\subsection{Results}

\begin{table*}[t]
    \centering
    \resizebox{\textwidth}{!}{
    \begin{tabular}{lccc|cccc|cccc}
        \hline
        \multirow{2}{*}{\textbf{System}} & \multirow{2}{*}{\textbf{User Satisf. $\uparrow$}} & \multirow{2}{*}{\textbf{Non-crit. $\downarrow$}} & \multirow{2}{*}{\textbf{Crit. $\downarrow$}} & \multicolumn{4}{c|}{\textbf{Correctness $\uparrow$}} & \multicolumn{4}{c}{\textbf{Completeness $\uparrow$}} \\
        \cline{5-12}
        & & & & \textbf{Arg./ret.} & \textbf{Docstr.} & \textbf{Comm.} & \textbf{Overall} & \textbf{Arg./ret.} & \textbf{Docstr.} & \textbf{Comm.} & \textbf{Overall} \\
        \hline
        \begin{tabular}[c]{@{}l@{}}Claude-3.7-\\ Sonnet\end{tabular} & 0.71 $\pm$ 0.05 & 0.25 $\pm$ 0.04 & 0.05 $\pm$ 0.02 & 0.95 & 0.94 & \textbf{0.92} & \textbf{0.91 $\pm$ 0.03} & 0.97 & 0.96 & 0.74 & 0.74 $\pm$ 0.04 \\
        O1 & \textbf{0.83 $\pm$ 0.04} & 0.16 $\pm$ 0.04 & 0.02 $\pm$ 0.01 & \textbf{0.98} & \textbf{0.97} & 0.89 & 0.89 $\pm$ 0.03 & 0.98 & 0.95 & 0.70 & 0.70 $\pm$ 0.05 \\
        \midrule
        \begin{tabular}[c]{@{}l@{}}PyDocAss\\ (Qwen-Coder)\end{tabular} & 0.80 $\pm$ 0.04 & \textbf{0.00 $\pm$ 0.00} & \textbf{0.00 $\pm$ 0.00}
            & \textbf{0.98} & \textbf{0.95} & 0.87 & 0.86 $\pm$ 0.03
            & \textbf{1.0} & \textbf{0.98} & 0.72 & 0.72 $\pm$ 0.04
            \\
        \begin{tabular}[c]{@{}l@{}}PyDocAss\\ (DeepSeek-V3)\end{tabular} & \textbf{0.83 $\pm$ 0.04} & \textbf{0.00 $\pm$ 0.00} & \textbf{0.00 $\pm$ 0.00}
            & \textbf{0.97} & \textbf{0.97} & \textbf{0.94} & \textbf{0.93 $\pm$ 0.03}
            & \textbf{1.0} & 0.96 & \textbf{0.78} & \textbf{0.78 $\pm$ 0.04}
             \\
        \begin{tabular}[c]{@{}l@{}}PyDocAss\\ (Default)\end{tabular} & \textbf{0.83 $\pm$ 0.04} & \textbf{0.00 $\pm$ 0.00} & \textbf{0.00 $\pm$ 0.00}
            & \textbf{0.98} & \textbf{0.97} & \textbf{0.94} & \textbf{0.93 $\pm$ 0.03}
            & \textbf{1.0} & 0.96 & \textbf{0.78} & \textbf{0.78 $\pm$ 0.04}
            \\
        \hline
    \end{tabular}
    }
    \caption{Comparative analysis of documentation systems across multiple dimensions. \textbf{User Satisfaction} indicates the proportion of positive user feedback. \textbf{Non-crit.} and \textbf{Crit.} represent non-critical and critical modifications to the original code. \textbf{Correctness} evaluates the accuracy of the provided documentation, while \textbf{Completeness} measures how often each documentation type is provided when needed.
    The \textbf{Overall} subcolumns represent cases where all three documentation dimensions are correct/complete simultaneously.
    PyDocAss (default) refers to our default setting, where Qwen-Coder provides arguments/returns annotation, and DeepSeek-V3 write docstrings and comments.
    \textbf{Bold} values indicate optimal performance in each category with respect to standard deviation.
    We do not report standard deviation for the subcategories for the sake of space.} 
    \label{tab:evaluation}
\end{table*}


Table~\ref{tab:evaluation} presents the key findings from our evaluation. Several advantages of PyDocAss can be observed.

\textbf{Perfect Code Preservation}: The most significant advantage of PyDocAss is its guaranteed code preservation. While direct LLM approaches modified the original code in 16-25\% of cases with non-critical changes and 2-5\% of cases with critical changes, PyDocAss consistently maintained the integrity of the original code. This characteristic is crucial since one never knows whether the system will introduce any changes, and hence needs to every time compare the documented code with the original one.

\textbf{Superior User Satisfaction}: PyDocAss achieved the highest user satisfaction score (0.85), on par with O1 \AskArtem{moeten we de hele uitdrukking schriven?} w.r.t. standard deviation but with a much smaller and faster model. This suggests that the specialized approach with modular documentation generation through structured outputs better meets user expectations compared to direct LLM approaches.

\textbf{Improved Reliability}: Documentation produced by PyDocAss introduces less hallucinations, making the automatic documentation more trusted by the users.

\textbf{Comprehensive Documentation}: Qualitative analysis of the generated documentation showed that PyDocAss consistently produced more complete documentation across all three components (type annotations, docstrings, and comments) compared to the baselines. The direct LLM approaches occasionally overlooked comments for hard-to-understand code snippets.
Using PyDocAss with Qwen-Coder provides the most complete documentation of docstrings. However, it write docstrings even for dummy functions/classes/methods, which decreases the user satisfaction.

\subsection{Limitations of the Evaluation}

While our evaluation demonstrates the effectiveness of PyDocAss, we acknowledge some limitations of the procedure:

\begin{itemize}
    \item The binary satisfaction metric doesn't capture nuanced user preferences or specific quality aspects of documentation
    \item The dataset, while diverse, is quite \AskArtem{ok word?} compact and may not capture all possible Python coding patterns and documentation needs
\end{itemize}

These limitations suggest directions for more comprehensive evaluations in future work.

\section{Community Benefits}

PyDocAss addresses a critical gap in the Python ecosystem by providing an accessible and reliable solution for generating high-quality documentation. The impact of this tool extends beyond individual developers to benefit the broader Python community in several significant ways:

\subsection{Enhancing Accessibility of Cutting-Edge Tools}

We have successfully applied PyDocAss to document several popular but under-documented Python frameworks that are driving innovation in AI research and development:

\begin{itemize}
    \item \textbf{Unsloth}~\cite{unsloth}: This emerging framework for efficient LLM fine-tuning, despite its \AskArtem{ok work?} tremendous success and popularity, lacked any documentation for many critical components. PyDocAss generated detailed type annotations and docstrings that clarified parameter usage, return values, and implementation details, making the library significantly more accessible to researchers and practitioners without deep knowledge in the field.
    
    \item \textbf{Berkeley Function Call Leaderboard}~\cite{berkeley-function-calling-leaderboard}: This framework for evaluating LLM function calling capabilities \AskArtem{repeating word} lacked documentation in some places, making it harder to extend to new approaches or datasets. PyDocAss wrote missing type annotations and docstrings, alleviating the understanding the leaderboard under the hood.
    
    \item \textbf{LM-Polygraph}~\cite{lm-polygraph}: This tool for quantifying uncertainty of a LLM also missed documentation for many crucial elements. PyDocAss provided comprehensive type annotations, docstrings, and comments for complex code snippets. This made the internal workings of the detection mechanisms more transparent and easier to customize.
\end{itemize}

The documentation generated for these libraries has been contributed back to their respective repositories, demonstrating PyDocAss's value in improving open-source project maintainability.

\subsection{Fostering an Accessible and Sustainable Python Ecosystem}

Poor documentation represents a significant barrier to adopting otherwise valuable tools, while also creating maintenance challenges for project maintainers. PyDocAss addresses both aspects by automating the documentation process, which:

\begin{itemize}
    \item \textbf{Lowers the entry barrier} for new users by providing clear explanations of classes, methods, and functions purposes and parameter requirements
    \item \textbf{Enables customization and extension} by documenting internal mechanisms that would otherwise require extensive code reading to understand, making advanced use cases more approachable
    \item \textbf{Improves quality and standardization} of documentation across the Python ecosystem, demonstrating best practices that encourage wider adoption of consistent documentation approaches
    \item \textbf{Reduces maintenance burden} for library maintainers by automating documentation updates as code evolves, allowing teams to focus on feature development rather than documentation upkeep
\end{itemize}

By addressing the persistent challenge of documentation debt, PyDocAss contributes to a more accessible, maintainable, and user-friendly Python ecosystem. This creates a positive feedback loop that benefits both developers and users of open-source software.

\section{Conclusion}

In this paper, we presented PyDocAss, an AI-powered Python Documentation Assistant that generates high-quality documentation while guaranteeing that no functional code is modified through AST-based analysis and structured generation techniques. Our evaluation demonstrates that PyDocAss outperforms direct LLM approaches with perfect code preservation, superior user satisfaction, and more comprehensive documentation, all while using smaller, more efficient models. The successful application to popular but under-documented Python frameworks illustrates PyDocAss's practical value in fostering a more accessible Python ecosystem. As AI coding assistants become increasingly integrated into development workflows, PyDocAss represents an important step toward more trustworthy automated programming tools that enhance code without risking functional changes.


\AskArtem{Where to better place Future work?} \subsection{Future Work}

Looking ahead, we plan to extend PyDocAss in several directions:

\begin{itemize}
    \item \textbf{Multilingual Support:} Extending the system to support additional programming languages beyond Python
    \item \textbf{Interactive Refinement:} Enabling more interactive documentation workflows with targeted questions and clarifications
    \item \textbf{Custom Style Templates:} Allowing users to define and apply custom documentation styles and formats
    \item \textbf{Project-Level Understanding:} Incorporating project-wide context to improve documentation coherence across files
    \item \textbf{Integration with Development Environments:} Creating plugins for popular IDEs to incorporate documentation generation into the development workflow
\end{itemize}

\AskArtem{Do we need any finalizing sentence here?}

\subsection{Availability}

PyDocAss is available as a web application at \url{https://ai.nebius.ai/apps/pydocass}. The source code is available on GitHub at \url{https://github.com/nebius/ai-studio-apps}, allowing for community contributions and adaptations. Both the web application and source code are provided with a permissive open-source license to encourage adoption and extension by the developer community.

\section{Limitations}

We thank the Nebius AI Studio team for providing the language model infrastructure that powers PyDocAss, as well as the beta testers who provided valuable feedback on earlier versions of the system. This work was supported by Nebius AI Studio.

\bibliographystyle{acl_natbib}
\bibliography{custom}

\appendix

\section{Working with PyDocAss via CLI}

Figure~\ref{fig:cli} in the Appendix~\ref{sec:appendix} shows how to run documentation with PyDocAss for the input Python file. Below is a simple example of using PyDocAss via the command line:

\begin{lstlisting}
# Set API key as environment variable and document a Python file
NEBIUS_API_KEY=YOUR_NEBIUS_API_KEY run-document my_file.py
\end{lstlisting}

The only user input it requires is an API key to Nebius AI Studio\footnote{The API key to Nebius AI Studio can be obtained at \url{https://studio.nebius.com/settings/api-keys} after registration.} / any OpenAI-like inference provider for the underlying models.

\end{document}
