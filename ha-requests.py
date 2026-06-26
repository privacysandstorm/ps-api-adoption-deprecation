import argparse


def plotCHIPS(df, figsDir):
    import matplotlib.dates as mdates

    sns.set_style("whitegrid")

    plot = sns.lineplot(
        df,
        x="date",
        y="partitionKey",
        markers=True,
        hue="type",
        style="type",
        # label="firstParty",
    )
    plt.legend(title="")

    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    plot.xaxis.set_major_locator(locator)
    plot.xaxis.set_major_formatter(formatter)
    plot.set(ylabel="% Partitioned cookies (CHIPS)")
    plot.set(xlabel="Date")

    saveFig(os.path.join(figsDir, "chips-percentage.pdf"))

    return


def log_formatter(x, pos):
    """
    Format tick labels as 10^value.
    x: The current tick value on the colorbar (the log value).
    pos: The position index (unused here).
    """
    # Only format if x >= 0 to avoid formatting -inf or errors
    if x >= 0:
        return r"$10^{{{:.0f}}}$".format(x)
    return ""


def plotAdopters(df, figsDir):
    from matplotlib.ticker import FuncFormatter

    columns = [
        "attribution",
        "fedcm",
        "fenced_frames",
        "floc",
        "private_aggregation",
        "private_state_tokens",
        "protected_audience",
        "shared_storage",
        "storage_access",
        "topics",
        "ua_client_hints",
    ]

    dates = df["date"].unique()
    for date in dates:

        data = df[df["date"] == date].set_index("host")[columns]
        # logscale

        data_log = np.log10(data + 1)  # add small value to handle null values
        plot = sns.heatmap(
            data_log,
            cbar_kws={
                # "label": "API Usage (log-scale)",
                "format": FuncFormatter(log_formatter),
            },
            cmap="magma_r",
        )
        plot.set_title(f"{date} (log-scale)", fontsize=8)
        plot.set_xlabel("", fontsize=8)
        plot.set_ylabel("Host", fontsize=8)
        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.yticks(fontsize=8)

        saveFig(
            os.path.join(figsDir, "heatmap-top10-" + str(date) + ".pdf"), size=[5, 3]
        )

    return


if __name__ == "__main__":
    # Create Argument Parser
    parser = argparse.ArgumentParser(
        prog="python3 ha-requests.py",
        description="Parse and plot results from HTTP Archive",
    )
    req_grp = parser.add_argument_group(title="Required arguments")
    req_grp.add_argument(
        "-plot",
        "--plot",
        help="Execution type: plot",
        choices=["CHIPS", "adopters"],
        required=True,
    )
    parser.add_argument(
        "-inputDir",
        "--inputDir",
        help="Input Directory",
        default="./data/ha-requests/",
    )
    parser.add_argument(
        "-figsDir",
        "--figsDir",
        help="Figs Directory",
        default="./figs/ha-requests/",
    )
    parser.add_argument(
        "-endDate",
        "--endDate",
        help="Keep only data for which date is before endDate",
        default="2026-05-01",
    )
    parser.add_argument(
        "-sampleRule",
        "--sampleRule",
        help="Sample rule to aggregate data, MS=monthly, QS=quarterly, etc.",
        default="QS",
    )
    parser.add_argument(
        "-logScale",
        "--logScale",
        help="Plot graph with logscale for y axis or not",
        default=True,
        action=argparse.BooleanOptionalAction,
    )
    args = parser.parse_args()

    import os

    from utils import (
        convertTicklabelsQuarters,
        saveFig,
    )

    os.makedirs(os.path.dirname(args.figsDir), exist_ok=True)

    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt
    import numpy as np
    import glasbey

    # set sns style
    sns.set_style("whitegrid")

    if args.plot == "CHIPS":
        df = pd.read_csv(
            os.path.join(args.inputDir, "attributes-cookies.tsv"),
            sep="\t",
            parse_dates=["date"],
        )
        df["partitionKey"] *= 100
        df["type"] = np.where(
            df["firstParty"] == True,
            "First-party",
            "Third-party",
        )
        plotCHIPS(df, args.figsDir)

    elif args.plot == "adopters":
        df = pd.read_csv(
            os.path.join(args.inputDir, "adopters-top10.tsv"),
            sep="\t",
            # parse_dates=["date"],
        )

        plotAdopters(df, args.figsDir)
