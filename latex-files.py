import argparse
from utils import normalizeAPINames


def formatReferences(cites):
    if cites and cites != []:
        refs = ""
        n = len(cites)
        i = 0
        for cite in cites:
            refs += cite
            if i != n - 1:
                refs += ","
            i += 1
        return r" \cite{" + refs + r"}"
    else:
        return "-"


def formatDate(date):
    if date:
        return date[:7]  # keep only year and month e.g., 2026-01
    else:
        return "-"


def formatCalls(apis):
    calls = ""
    n = len(apis)
    nlines = 0
    i = 0
    count = 0
    for api in apis:
        i += 1
        count += len(api)
        if count > 33:
            count = len(api)
            calls += "\\\\"
            nlines += 1
            calls += "\\texttt{" + api + "}"
        else:
            calls += "\\texttt{" + api + "}"
        if n > i and nlines == 1:
            calls += ", ..."
            break
        if i != len(apis):
            calls += ", "
    return calls


def backgroundTable(
    apis,
    inputDir,
    outputDir,
):
    # sort for table order
    apisSorted = sorted(
        apis["apis"],
        key=lambda x: (
            np.datetime64(x["shipping"]),
            np.datetime64(x["testing"]),
            x["name"],
        ),
    )

    with open(inputDir + "background-table-start.tex", "r") as input:
        apisStart = input.read()

    with open(outputDir + "background-table.tex", "w") as output:
        output.write(apisStart)

        for api in apisSorted:
            if api["name"] != "extra":
                output.write(
                    "\n{}".format(
                        r"\texttt{"
                        + api["name"]
                        + r"}"
                        + formatReferences(api["explainer"])
                    )
                )
                output.write(" & {}".format(api["use-case"]))
                output.write(" & {}".format(formatDate(api["testing"])))
                output.write(" & {}".format(formatDate(api["shipping"])))
                output.write(" & {}".format(formatDate(api["deprecation"])))
                # related work
                output.write(" & {}".format(formatReferences(api["measurement-work"])))
                output.write(" & {}".format(formatReferences(api["other-work"])))
                output.write(r"\\" + "\n")
        output.write(
            "\n" + r"\bottomrule" + "\n" + r"\end{tabular}" + "\n" + r"\end{table*}"
        )

    return


def appendixList(apis, outputDir):

    apisSorted = sorted(
        apis["apis"],
        key=lambda x: (x["name"],),
    )

    with open(outputDir + "apis-appendix.tex", "w") as output:
        for api in apisSorted:
            if api["name"] != "extra" and api["name"] != "RWS":

                output.write(
                    "\n" + r"\subsection{\texttt{" + api["name"] + r"}}" + "\n"
                )
                apiCalls = ""

                if api["JS"] != []:
                    if len(api["JS"]) > 1:
                        output.write(r"\noindent\textbf{JavaScript APIs}:" + "\n")
                    else:
                        output.write(r"\noindent\textbf{JavaScript API}:" + "\n")
                    output.write(r"\begin{itemize}\footnotesize" + "\n")
                    for call in api["JS"]:
                        output.write(r"\item \texttt{" + call + r"}" + "\n")
                    output.write(r"\end{itemize}" + "\n")

                if api["HTTP"] != []:
                    if len(api["HTTP"]) > 1:
                        output.write(r"\noindent\textbf{HTTP headers}:" + "\n")
                    else:
                        output.write(r"\noindent\textbf{HTTP header}:" + "\n")
                    output.write(r"\begin{itemize}\footnotesize" + "\n")
                    for call in api["HTTP"]:
                        output.write(r"\item \texttt{" + call + r"}" + "\n")
                    output.write(r"\end{itemize}" + "\n")

                # exclude if no feature
                if api["kFeatures"]:
                    lowercaseName = normalizeAPINames(api["name"])

                    output.write(r"\begin{figure}[!h]" + "\n")
                    output.write(r"\centering" + "\n")
                    output.write(
                        (
                            r"\includegraphics[width=\linewidth]{figs/telemetry/"
                            + lowercaseName
                            + r"-QS.pdf}"
                            + "\n"
                        )
                    )
                    output.write(
                        (r"\caption{\texttt{" + api["name"] + r"} features.}" + "\n")
                    )
                    output.write(r"\label{fig:appendix-" + lowercaseName + r"}" + "\n")
                    output.write(r"\end{figure}" + "\n")

    return


def appendixTable(apis, outputDir):

    apisSorted = sorted(
        apis["apis"],
        key=lambda x: (x["name"],),
    )

    with open(outputDir + "appendix-apis-table.tex", "w") as output:

        output.write(
            r"\begin{table*}[!ht]"
            + "\n"
            + r"\centering"
            + "\n"
            + r"\fontsize{6}{6}"
            + "\n"
            + r"\setlength{\tabcolsep}{2pt}"
            + "\n"
            + r"\renewcommand{\arraystretch}{0.3}"
            + "\n"
            + r"\begin{tabularx}{\textwidth}{p{4.35cm} Y Y }"
            + "\n"
            + r"\toprule"
            + "\n"
            + r"\textbf{\footnotesize Permissions Policy Directives} & \textbf{\footnotesize JavaScript Methods} & \textbf{\footnotesize HTTP Headers} \\"
            + "\n"
            + r"\midrule"
            + "\n"
        )
        for api in apisSorted:
            if api["name"] != "extra":

                # output.write(
                #     "\n"
                #     # + r"\addlinespace[2pt]\\"
                #     # + "\n"
                #     + r"\multicolumn{3}{l}{\footnotesize \textbf{"
                #     + api["name"]
                #     + r"}}\\"
                #     + "\n"
                # )

                apiCalls = ""
                output.write(r"\begin{itemize}[leftmargin=0pt, label={}]" + "\n")
                output.write(
                    r"\item \textbf{\footnotesize " + api["name"] + r"}" + "\n"
                )
                if api["permission"] != []:
                    for permission in api["permission"]:
                        output.write(r"\item \texttt{" + permission + r"}" + "\n")
                else:
                    output.write(r"\item \texttt{-}" + "\n")
                output.write(r"\end{itemize}" + "\n")

                output.write("&\n")

                output.write(r"\begin{itemize}[leftmargin=0pt, label={}]" + "\n")
                if api["JS"] != []:
                    for call in api["JS"]:
                        output.write(r"\item \texttt{" + call + r"}" + "\n")
                else:
                    output.write(r"\item \texttt{-}" + "\n")
                output.write(r"\end{itemize}" + "\n")

                output.write("&\n")

                output.write(r"\begin{itemize}[leftmargin=0pt, label={}]" + "\n")
                if api["HTTP"] != []:
                    for call in api["HTTP"]:
                        output.write(r"\item \texttt{" + call + r"}" + "\n")
                else:
                    output.write(r"\item \texttt{-}" + "\n")
                output.write(r"\end{itemize}" + "\n")

                output.write(r"\\" + "\n" + r"\addlinespace[2pt]\\" + "\n")
        output.write(
            r"\bottomrule"
            + "\n"
            + r"\end{tabularx}"
            + "\n"
            + r"\caption{Permissions policy directives, JavaScript methods, and HTTP headers (if any) measured in this paper for each proposal. The list is also available in our artifact in \texttt{.JSON} format (see~\refappendix{sec:open-science}).}"
            + "\n"
            + r"\label{tab:appendix-apis-table}"
            + "\n"
            + r"\end{table*}"
            + "\n"
        )

    return


if __name__ == "__main__":
    # Create Argument Parser
    parser = argparse.ArgumentParser(
        prog="python3 latex-files.py",
        description="Generate some of the latex tables and appendix for paper",
    )
    parser.add_argument(
        "-jsonAPIs",
        "--jsonAPIs",
        help="APIs input json file",
        default="./apis.json",
    )
    parser.add_argument(
        "-inputDir",
        "--inputDir",
        help="Input directory",
        default="./data/",
    )
    parser.add_argument(
        "-outputDir",
        "--outputDir",
        help="Output directory",
        default="./figs/",
    )
    args = parser.parse_args()

    import json
    import numpy as np
    import os

    if not (os.path.isfile(args.jsonAPIs)):
        raise Exception("Error: file(s) missing")
    else:
        # Automatically create the output directory hierarchy if needed
        os.makedirs(os.path.dirname(args.outputDir), exist_ok=True)
        # get apis from json
        with open(args.jsonAPIs, "r") as f:
            apis = json.load(f)

        # output background table
        backgroundTable(apis, args.inputDir, args.outputDir)

        # output appendix list
        appendixList(apis, args.outputDir)

        appendixTable(apis, args.outputDir)
