import argparse


def getFeatureAPINames(apis):
    ids = []
    featureNames = []
    apiNames = []
    for api in apis["apis"]:
        kFeatures = api["kFeatures"]
        if kFeatures != None:
            for feature in kFeatures:
                ids.append(feature["id"])
                featureNames.append(feature["name"])
                apiNames.append(api["name"])
    dfeatures = pd.DataFrame({"id": ids, "feature": featureNames, "api": apiNames})
    return dfeatures


def plotIndividualAPIs(
    apis,
    data,
    figsDir,
    endDate,
    logScale,
    sampleRule,
    clipLower,
    addDates,
):
    dfeatures = getFeatureAPINames(apis)
    df = data.merge(dfeatures, on="id")
    df["percentage"] = df["num_urls"] / df["total_urls"] * 100
    # remplace Nan values in rank with max(rank) for earlier dates
    df.fillna(value={"rank": df["rank"].max()}, inplace=True)

    for api in apis["apis"]:
        if api["kFeatures"] == None:
            continue
        nColumns = api["plotOptions"]["nColumns"]
        figSize = [api["plotOptions"]["sizeX"], api["plotOptions"]["sizeY"]]

        print(api["name"])
        # get dataframe
        dff = (
            df[df["api"] == api["name"]]
            .drop(columns=["api", "num_urls", "total_urls", "id"])
            .reset_index(drop=True)
        )
        if not (dff.empty):
            # keep only data before endDate and aggregate following sampleRule
            dff = (
                dff[dff["date"] < np.datetime64(endDate)]
                .groupby(["feature", "client", "rank"])
                .resample(sampleRule, on="date")
                .mean()
                .reset_index()
            )
            # clip data below threshold to avoid weird artifacts on log graph
            dff["percentage"] = dff["percentage"].clip(lower=clipLower)

            # keep last only
            dff = (
                dff.sort_values(["rank"])
                .groupby(["feature", "client", "date"])
                .last()
                .reset_index()
            )

            # sort first by date (otherwise when we convert date to quarter and back to string, things are sometimes out of order)
            data = dff.sort_values(["date"])
            dateMin = data["date"].min()
            dateMax = data["date"].max()

            data["date"] = data["date"].dt.to_period("Q").astype("string")

            plot = sns.lineplot(
                data=data,
                x="date",
                y="percentage",
                hue="feature",
                hue_order=np.sort(data["feature"].unique()),
                palette=glasbey.create_palette(
                    palette_size=data["feature"].nunique(),
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
                # title="Feature",
                frameon=False,
            )

            if logScale:
                plt.yscale("log")
                lowercaseName = normalizeAPINames(api["name"]) + "-log"
            else:
                lowercaseName = normalizeAPINames(api["name"])

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
    apis,
    data,
    figsDir,
    endDate,
    logScale,
    sampleRule,
    clipLower,
    addDates,
    excludeDeprecatedAPIs,
):

    dfeatures = getFeatureAPINames(apis)
    df = data.merge(dfeatures, on="id")
    df["percentage"] = df["num_urls"] / df["total_urls"] * 100
    # remplace Nan values in rank with max(rank) for earlier dates
    df.fillna(value={"rank": df["rank"].max()}, inplace=True)

    # number columns caption
    ncolumns = 4
    # exclude "extra" (kPrivacySandboxAdsAPIs edge case)
    df = (
        df[df["api"] != "extra"]
        .drop(columns=["num_urls", "total_urls", "id", "feature"])
        .reset_index(drop=True)
    )
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
    df = df.groupby(["api", "client", "rank", "date"])["percentage"].max().reset_index()

    # keep last only
    df = (
        df.sort_values(["rank"]).groupby(["api", "client", "date"]).last().reset_index()
    )

    # keep only data before endDate and aggregate following sampleRule
    df = (
        df[df["date"] < np.datetime64(endDate)]
        .groupby(["api", "client"])
        .resample(sampleRule, on="date")
        .mean()
        .reset_index()
    )
    # clip data below threshold to avoid weird artifacts on log graph
    df["percentage"] = df["percentage"].clip(lower=clipLower)

    # sort first by date (otherwise when we convert date to quarter and back to string, things are sometimes out of order)
    data = df.sort_values(["date"])
    dateMin = data["date"].min()
    dateMax = data["date"].max()
    data["date"] = data["date"].dt.to_period("Q").astype("string")

    plot = sns.lineplot(
        data=data,
        x="date",
        y="percentage",
        hue="api",
        hue_order=np.sort(data["api"].unique()),
        palette=glasbey.create_palette(
            palette_size=data["api"].nunique(),
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
        # title="API",
        frameon=False,
    )

    if logScale:
        plt.yscale("log")
        lowercaseName = "all-apis-upper-envelope-log"
    else:
        lowercaseName = "all-apis-upper-envelope"

    # format xticks labels to quarters  +year below Q1
    _, labels = plt.xticks()
    plot.xaxis.set_ticklabels(convertTicklabelsQuarters(labels))
    plot.set(ylabel="% page loads")

    saveFig(
        figsDir + lowercaseName + "-" + sampleRule + ".pdf",
        size=[8, 4],
    )

    return


def mergeAll(dfusage, apis, mergedDir):
    """Merge per API and for all APIs"""
    # compute percentage
    dfusage["percentage"] = dfusage["num_urls"] / dfusage["total_urls"] * 100
    # drop columns for smaller size file
    dfusage = dfusage.drop(columns=["num_urls", "total_urls"])
    dfapis = []
    for api in apis["apis"]:
        dfs = []
        kFeatures = api["kFeatures"]
        # do not do anything if null
        if kFeatures != None:
            for feature in kFeatures:
                # get data
                df = dfusage[dfusage["id"] == feature["id"]]
                if not (df.empty):
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
                # add API name
                dfapi["api"] = api["name"]
                dfapis.append(dfapi)
    # dump into .tsv
    pd.concat(dfapis, ignore_index=True).to_csv(
        mergedDir + "all.tsv", sep="\t", index=False
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
            # keep max rank for each date
            df = (
                df.sort_values(["rank"])
                .groupby(["feature", "client", "date"])
                .last()
                .reset_index()
            )
            # max only across features
            df = df.groupby(["date", "client"])["percentage"].max().reset_index()
            # resample per quarter, groupping by client
            df = (
                df[df["date"] < np.datetime64(endDate)]
                .groupby(["client"])
                .resample(sampleRule, on="date")
                .mean()
                .reset_index()
            )
            # for client in ["desktop", "mobile"]:
            #     data = df[df["client"] == client]
            #     # convert date to quarter string
            #     data = data.sort_values(["date"])
            #     data["date"] = data["date"].dt.to_period("Q").astype("string")

            # convert date to quarter string
            df = df.sort_values(["client", "date"])
            df["date"] = df["date"].dt.to_period("Q").astype("string")
            df = df[df["date"].isin(quarters)]
            print(apiName)
            print(df)
            print("\n")

    return


def printStats(mergedDir, endDate):
    """Return general stats about dataset"""
    df = pd.read_csv(
        mergedDir + "all.tsv",
        sep="\t",
        parse_dates=["date"],
    )
    # remove extra
    df = df[df["api"] != "extra"]

    # keep max rank for each date
    df = (
        df.sort_values(["rank"])
        .groupby(["feature", "client", "date"])
        .last()
        .reset_index()
    )

    print("Nb features per API")
    print(df.groupby(["client", "api"])["feature"].nunique())
    print("\n")

    print("Nb datapoints per API")
    print(df.groupby(["client", "api"])["percentage"].count())
    print("\n")

    print("Nb unique crawls per API")
    print(df.groupby(["client", "api"])["date"].nunique())
    print("\n")

    print("Min date per API")
    print(df.groupby(["client", "api"])["date"].min())
    print("\n")

    print("Max date per API")
    print(df.groupby(["client", "api"])["date"].max())
    print("\n")

    print("Total stats")
    print("Nb features: {}".format(df.groupby(["client"])["feature"].nunique()))
    print(
        "Nb data points total: {}".format(df.groupby(["client"])["percentage"].count())
    )
    print("Nb unique crawls: {}".format(df.groupby(["client"])["date"].nunique()))
    print("Min day: {}".format(df.groupby(["client"])["date"].min()))
    print("Max day: {}".format(df.groupby(["client"])["date"].max()))

    print("--Max usage per quarter--")
    # max only
    df = df.groupby(["api", "client", "date"])["percentage"].max().reset_index()
    # resample per quarter
    df = (
        df[df["date"] < np.datetime64(endDate)]
        .groupby(["api", "client"])
        .resample("QS", on="date")
        .mean()
        .reset_index()
    )

    print("Max percentage per API")
    print(df.groupby(["client", "api"])["percentage"].max())
    print("\n")

    return


if __name__ == "__main__":
    # Create Argument Parser
    parser = argparse.ArgumentParser(
        prog="python3 ha-blink.py",
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
        default="./data/ha-blink/",
    )
    parser.add_argument(
        "-mergedDir",
        "--mergedDir",
        help="Merged Directory",
        default="./data/ha-blink/merged/",
    )
    parser.add_argument(
        "-figsDir",
        "--figsDir",
        help="Figs Directory",
        default="./figs/ha-blink/",
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

        # set sns style
        sns.set_style("whitegrid")
        with open(args.jsonAPIs) as f:
            apis = json.load(f)

        if args.type == "merge":

            df = pd.read_csv(
                os.path.join(args.inputDir, "kfeatures-usage.csv"),
                parse_dates=["date"],
            )
            mergeAll(df, apis, args.mergedDir)

        if args.type == "plotAll":
            import matplotlib.pyplot as plt
            import numpy as np
            import glasbey

            df = pd.read_csv(
                os.path.join(args.inputDir, "kfeatures-usage.csv"),
                parse_dates=["date"],
            )

            plotIndividualAPIs(
                apis,
                df,
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

            df = pd.read_csv(
                os.path.join(args.inputDir, "kfeatures-usage.csv"),
                parse_dates=["date"],
            )

            plotUpperEnvelope(
                apis,
                df,
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
            printStats(args.mergedDir, args.endDate)
