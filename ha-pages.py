import argparse


def cumSumPerRank(df, columns_groupby, column_to_sum_on):
    """Return cumulative sum of total pages per rank for each date, client, and is_root_page"""
    ranks = np.sort(df["rank"].unique())
    dfranks = []
    for rank in ranks:
        dfrank = (
            df.loc[df["rank"] <= rank]
            .groupby(columns_groupby)[column_to_sum_on]
            .sum()
            .reset_index()
        )
        dfrank["rank"] = rank
        dfranks.append(dfrank)

    return pd.concat(dfranks, ignore_index=True)


def mergeAll(jsonAPIs, dffeatures, dfpages, mergedDir):
    """Merge per API and for all APIs"""

    with open(jsonAPIs) as f:
        apis = json.load(f)

    dfapis = []
    for api in apis["apis"]:
        dfs = []
        kFeatures = api["kFeatures"]
        # do not do anything if null
        if kFeatures != None:
            for feature in kFeatures:
                # add api name in dffeatures
                dffeatures.loc[dffeatures["id"] == feature["id"], ["api"]] = api["name"]
                # get data
                df = dffeatures[dffeatures["id"] == feature["id"]]
                if not (df.empty):
                    # count unique nb of pages feature is detected on
                    df = (
                        df.groupby(["date", "client", "is_root_page", "rank"])["page"]
                        .nunique()
                        .reset_index()
                    )
                    # cumulative sum per rank
                    df = cumSumPerRank(df, ["date", "client", "is_root_page"], "page")
                    # merge with cumulative sum
                    df = df.merge(
                        dfpages,
                        left_on=["date", "client", "is_root_page", "rank"],
                        right_on=["date", "client", "is_root_page", "rank_grouping"],
                    )
                    # compute percentage
                    df["percentage"] = df["page"] / df["total_pages"] * 100
                    # add feature name
                    df["feature"] = feature["name"]
                    dfs.append(df)

            if dfs != []:
                dfapi = pd.concat(dfs, ignore_index=True)
                # dump into .tsv
                dfapi.to_csv(
                    mergedDir + normalizeAPINames(api["name"]) + ".tsv",
                    sep="\t",
                    index=False,
                )

    # once loop is over aggregate dffeatures by api name and count nunique pages
    dfapis = (
        dffeatures.groupby(["api", "date", "client", "is_root_page", "rank"])["page"]
        .nunique()
        .reset_index()
    )
    # cumulative sum per rank
    dfapis = cumSumPerRank(dfapis, ["api", "date", "client", "is_root_page"], "page")
    # merge with cumulative sum
    dfapis = dfapis.merge(
        dfpages,
        left_on=["date", "client", "is_root_page", "rank"],
        right_on=["date", "client", "is_root_page", "rank_grouping"],
    )
    # compute percentage
    dfapis["percentage"] = dfapis["page"] / dfapis["total_pages"] * 100

    # dump into .tsv
    dfapis.to_csv(mergedDir + "all.tsv", sep="\t", index=False)
    return


def plotIndividualAPIs(
    jsonAPIs,
    mergedDir,
    figsDir,
    endDate,
    logScale,
    sampleRule,
    clipLower,
    addDates,
):
    """Plot graphs for individual APIs"""
    # set sns style
    sns.set_style("whitegrid")
    with open(jsonAPIs) as f:
        apis = json.load(f)

    for api in apis["apis"]:
        if api["kFeatures"] == None:
            continue
        nColumns = api["plotOptions"]["nColumns"]
        figSize = [api["plotOptions"]["sizeX"], api["plotOptions"]["sizeY"]]

        if os.path.isfile(mergedDir + normalizeAPINames(api["name"]) + ".tsv"):
            # get the dataframe
            df = pd.read_csv(
                mergedDir + normalizeAPINames(api["name"]) + ".tsv",
                sep="\t",
                parse_dates=["date"],
            ).drop(columns=["page", "total_pages"])

            # keep last only (drop rank)
            df = (
                df.sort_values(["rank"])
                .groupby(["feature", "client", "date", "is_root_page"])
                .last()
                .reset_index()
            ).drop(columns=["rank"])

            for is_root_page in [True, False]:
                dff = df[df["is_root_page"] == is_root_page]
                lowercaseName = "root-" if is_root_page else "secondary-"

                # keep only data before endDate and aggregate following sampleRule
                dff = (
                    dff[dff["date"] < np.datetime64(endDate)]
                    .groupby(["feature", "client", "is_root_page"])
                    .resample(sampleRule, on="date")
                    .mean()
                    .reset_index()
                )
                # clip data below threshold to avoid weird artifacts on log graph
                dff["percentage"] = dff["percentage"].clip(lower=clipLower)

                # sort first by date (otherwise when we convert date to quarter and back to string, things are sometimes out of order)
                dff = dff.sort_values(["date"])
                dateMin = dff["date"].min()
                dateMax = dff["date"].max()
                dff["date"] = dff["date"].dt.to_period("Q").astype("string")

                plot = sns.lineplot(
                    data=dff,
                    x="date",
                    y="percentage",
                    hue="feature",
                    hue_order=np.sort(df["feature"].unique()),
                    palette=glasbey.create_palette(
                        palette_size=df["feature"].nunique(),
                        colorblind_safe=True,
                        optimize_palette_search_radius=50,
                    ),  # type: ignore
                    markers=True,
                    style="client",
                    dashes=True,
                )

                # add vertical lines to highlight important dates
                if addDates:
                    addVerticalDates(dateMin, dateMax)

                # move legend to not overlap with figure
                sns.move_legend(
                    plot,
                    "lower center",  # "best"
                    bbox_to_anchor=(0.5, 1),
                    ncol=nColumns,
                    fontsize="small",
                    title="{}".format(
                        "On root pages" if is_root_page else "On secondary pages"
                    ),
                    frameon=False,
                )

                if logScale:
                    plt.yscale("log")
                    lowercaseName += normalizeAPINames(api["name"]) + "-log"
                else:
                    lowercaseName += normalizeAPINames(api["name"])

                # format xticks labels to quarters  +year below Q1
                _, labels = plt.xticks()
                plot.xaxis.set_ticklabels(convertTicklabelsQuarters(labels))
                plot.set(ylabel="% page loads")

                saveFig(
                    figsDir + lowercaseName + "-" + sampleRule + ".pdf",
                    size=figSize,
                )

    return


def plotUpperEnvelope(
    mergedDir,
    figsDir,
    endDate,
    logScale,
    sampleRule,
    clipLower,
    addDates,
    excludeDeprecatedAPIs,
):
    """Plot the upper envelope for each API"""
    # set sns style
    sns.set_style("whitegrid")
    # load dataframe
    df = pd.read_csv(
        mergedDir + "all.tsv",
        sep="\t",
        parse_dates=["date"],
    )
    # number columns caption
    ncolumns = 4
    # exclude "extra" (kPrivacySandboxAdsAPIs edge case)
    df = df[df["api"] != "extra"]
    # excludeapis not supported anymore
    if excludeDeprecatedAPIs:
        df = df[df["api"] != "FLoC"]
        df = df[df["api"] != "Attribution Reporting"]
        df = df[df["api"] != "Private Aggregation"]
        df = df[df["api"] != "Protected Audience"]
        df = df[df["api"] != "RWS"]
        df = df[df["api"] != "Shared Storage"]
        df = df[df["api"] != "Topics"]
        ncolumns = 3

    # keep maximum only for upper envelope
    df = (
        df.groupby(["api", "client", "rank", "date", "is_root_page"])["percentage"]
        .max()
        .reset_index()
    )

    # keep last only
    df = (
        df.sort_values(["rank"])
        .groupby(["api", "client", "date", "is_root_page"])
        .last()
        .reset_index()
    )

    for is_root_page in [True, False]:
        dff = df[df["is_root_page"] == is_root_page]
        lowercaseName = "root-" if is_root_page else "secondary-"

        # keep only data before endDate and aggregate following sampleRule
        dff = (
            dff[dff["date"] < np.datetime64(endDate)]
            .groupby(["api", "client", "is_root_page"])
            .resample(sampleRule, on="date")
            .mean()
            .reset_index()
        )
        # clip data below threshold to avoid weird artifacts on log graph
        dff["percentage"] = dff["percentage"].clip(lower=clipLower)

        # sort first by date (otherwise when we convert date to quarter and back to string, things are sometimes out of order)
        dff = dff.sort_values(["date"])
        dateMin = dff["date"].min()
        dateMax = dff["date"].max()
        dff["date"] = dff["date"].dt.to_period("Q").astype("string")

        plot = sns.lineplot(
            data=dff,
            x="date",
            y="percentage",
            hue="api",
            hue_order=np.sort(df["api"].unique()),
            palette=glasbey.create_palette(
                palette_size=df["api"].nunique(),
                colorblind_safe=True,
                optimize_palette_search_radius=50,
            ),  # type: ignore
            markers=True,
            style="client",
            dashes=True,
        )

        # add vertical lines to highlight important dates
        if addDates:
            addVerticalDates(dateMin, dateMax)

        # move legend to not overlap with figure
        sns.move_legend(
            plot,
            "lower center",  # "best"
            bbox_to_anchor=(0.5, 1),
            ncol=ncolumns,
            fontsize="small",
            title="{}".format(
                "On root pages" if is_root_page else "On secondary pages"
            ),
            frameon=False,
        )

        if logScale:
            plt.yscale("log")
            lowercaseName += "all-apis-upper-envelope" + "-log"
        else:
            lowercaseName += "all-apis-upper-envelope"

        # format xticks labels to quarters  +year below Q1
        _, labels = plt.xticks()
        plot.xaxis.set_ticklabels(convertTicklabelsQuarters(labels))
        plot.set(ylabel="% page loads")

        saveFig(
            figsDir + lowercaseName + "-" + sampleRule + ".pdf",
            size=[8, 4],
        )

    return


def printUsage(apiNames, quarters, mergedDir, endDate, sampleRule):
    """Return max page load usage for specified quarters and APIs"""

    print("Usage of non-deprecated APIs in past quarters")

    for apiName in apiNames:
        if os.path.isfile(mergedDir + normalizeAPINames(apiName) + ".tsv"):
            df = pd.read_csv(
                mergedDir + normalizeAPINames(apiName) + ".tsv",
                sep="\t",
                parse_dates=["date"],
            )
            # keep last rank for each date
            df = (
                df.sort_values(["rank"])
                .groupby(["feature", "is_root_page", "client", "date"])
                .last()
                .reset_index()
            )
            # max only across features
            df = (
                df.groupby(["is_root_page", "client", "date"])["percentage"]
                .max()
                .reset_index()
            )
            # resample per quarter, groupping by client
            df = (
                df[df["date"] < np.datetime64(endDate)]
                .groupby(["is_root_page", "client"])
                .resample(sampleRule, on="date")
                .mean()
                .reset_index()
            )

            # convert date to quarter string
            df = df.sort_values(
                [
                    "is_root_page",
                    "client",
                    "date",
                ]
            )
            df["date"] = df["date"].dt.to_period("Q").astype("string")
            df = df[df["date"].isin(quarters)]
            print(apiName)
            print(df)
            print("\n")

    return


def printStats(mergedDir, apiNames):
    """Return general stats about dataset"""
    dfs = []

    for apiName in apiNames:
        if os.path.isfile(mergedDir + normalizeAPINames(apiName) + ".tsv"):
            df = pd.read_csv(
                mergedDir + normalizeAPINames(apiName) + ".tsv",
                sep="\t",
                parse_dates=["date"],
            )
            # keep last rank for each date
            df = (
                df.sort_values(["rank"])
                .groupby(["feature", "client", "date", "is_root_page"])
                .last()
                .reset_index()
            )
            df["api"] = apiName
            dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

    # remove extra
    df = df[df["api"] != "extra"]

    print("Nb features per API")
    print(
        df.groupby(
            [
                "is_root_page",
                "client",
                "api",
            ]
        )["feature"].nunique()
    )
    print("\n")

    print("Nb datapoints per API")
    print(df.groupby(["is_root_page", "client", "api"])["percentage"].count())
    print("\n")

    print("Nb unique crawls per API")
    print(df.groupby(["is_root_page", "client", "api"])["date"].nunique())
    print("\n")

    print("Min date per API")
    print(df.groupby(["is_root_page", "client", "api"])["date"].min())
    print("\n")

    print("Max date per API")
    print(df.groupby(["is_root_page", "client", "api"])["date"].max())
    print("\n")

    print("Total stats")
    print(
        "Nb features: {}".format(
            df.groupby(["is_root_page", "client"])["feature"].nunique()
        )
    )
    print(
        "Nb data points total: {}".format(
            df.groupby(["is_root_page", "client"])["percentage"].count()
        )
    )
    print(
        "Nb unique crawls: {}".format(
            df.groupby(["is_root_page", "client"])["date"].nunique()
        )
    )
    print("Min day: {}".format(df.groupby(["is_root_page", "client"])["date"].min()))
    print("Max day: {}".format(df.groupby(["is_root_page", "client"])["date"].max()))

    return


if __name__ == "__main__":
    # Create Argument Parser
    parser = argparse.ArgumentParser(
        prog="python3 ha-pages.py",
        description="Parse and plot results from HTTP Archive",
    )
    req_grp = parser.add_argument_group(title="Required arguments")
    req_grp.add_argument(
        "-type",
        "--type",
        help="Execution type: aggregate, plot",
        choices=["merge", "plotAll", "plotMax", "stats"],
        required=True,
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
        help="Input Directory",
        default="./data/ha-pages/",
    )
    parser.add_argument(
        "-mergedDir",
        "--mergedDir",
        help="Merged Directory",
        default="./data/ha-pages/merged/",
    )
    parser.add_argument(
        "-figsDir",
        "--figsDir",
        help="Figs Directory",
        default="./figs/ha-pages/",
    )
    parser.add_argument(
        "-clipLower",
        "--clipLower",
        help="Drop aggregated percentage below this threshold",
        default=10**-6,
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
    parser.add_argument(
        "-addDates",
        "--addDates",
        help="Add vertical date markers to graph",
        default=True,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "-excludeDeprecatedAPIs",
        "--excludeDeprecatedAPIs",
        help="Do not plot deprecated APIs",
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "-nbInputFiles",
        "--nbInputFiles",
        help="Number of input files",
        default=13,
    )
    args = parser.parse_args()

    import os

    from utils import (
        addVerticalDates,
        convertTicklabelsQuarters,
        normalizeAPINames,
        saveFig,
    )

    if not (os.path.isfile(args.jsonAPIs)):
        raise Exception("Error: file(s) missing")
    else:
        # Automatically create the output directory hierarchy if needed
        os.makedirs(os.path.dirname(args.figsDir), exist_ok=True)
        os.makedirs(os.path.dirname(args.mergedDir), exist_ok=True)

        import pandas as pd
        import json
        import seaborn as sns

        if args.type == "merge":

            import numpy as np

            dfs = []
            for i in range(args.nbInputFiles):
                if i < 10:
                    suffix = "0" + str(i)
                else:
                    suffix = i
                df = pd.read_csv(
                    os.path.join(
                        args.inputDir, "kfeatures-pages-0000000000{}.csv".format(suffix)
                    ),
                    parse_dates=["date"],
                )
                dfs.append(df)
            dffeatures = pd.concat(dfs, ignore_index=True)

            dfpages = pd.read_csv(
                os.path.join(args.inputDir, "pages-totals.csv".format(i)),
                parse_dates=["date"],
            )

            mergeAll(args.jsonAPIs, dffeatures, dfpages, args.mergedDir)

        if args.type == "plotAll":
            import matplotlib.pyplot as plt
            import numpy as np
            import glasbey

            plotIndividualAPIs(
                args.jsonAPIs,
                args.mergedDir,
                args.figsDir,
                args.endDate,
                args.logScale,
                args.sampleRule,
                args.clipLower,
                args.addDates,
            )

        if args.type == "plotMax":
            import matplotlib.pyplot as plt
            import numpy as np
            import glasbey

            plotUpperEnvelope(
                args.mergedDir,
                args.figsDir,
                args.endDate,
                args.logScale,
                args.sampleRule,
                args.clipLower,
                args.addDates,
                args.excludeDeprecatedAPIs,
            )

        elif args.type == "stats":

            import numpy as np
            import pandas as pd

            apiNames = [
                "CHIPS",
                "FedCM",
                "Fenced Frames",
                "Private State Tokens",
                "Storage Access",
                "UA Client Hints",
            ]
            quarters = ["2025Q2", "2025Q3", "2025Q4", "2026Q1"]

            printUsage(
                apiNames, quarters, args.mergedDir, args.endDate, args.sampleRule
            )
            printStats(
                args.mergedDir,
                [
                    "Attribution Reporting",
                    "CHIPS",
                    "FedCM",
                    "Fenced Frames",
                    "FLoC",
                    "Private Aggregation",
                    "Private State Tokens",
                    "Protected Audience",
                    "Shared Storage",
                    "Storage Access",
                    "Topics",
                    "UA Client Hints",
                ],
            )
