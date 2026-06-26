import argparse


def downloadParse(bucketId, propertyName, outputDir):
    """Download the data corresponding to the provided bucketID from chromestatus"""
    import requests

    print("Downloading data for %s" % propertyName)
    response = json.loads(
        requests.get(
            "https://chromestatus.com/data/timeline/featurepopularity?bucket_id=%s"
            % (bucketId)
        ).text
    )
    # Parse to create valid file, check if propertyName is not "ERROR"
    days = set()
    data = {}

    for item in response:
        if ("k" + item["property_name"]) != "ERROR":
            days.add(item["date"])
            data[item["date"]] = item["day_percentage"]

    with open(outputDir + str(bucketId) + ".json", "w") as f:
        json.dump([{"date": k, "day_percentage": v} for k, v in data.items()], f)

    return


def downloadAll(jsonAPIs, outputDir):
    """Download all features for all APIs"""
    # Load APIs json file
    with open(jsonAPIs) as f:
        apis = json.load(f)
    # Download feature telemetry data for each API
    for api in apis["apis"]:
        kFeatures = api["kFeatures"]
        # stop if null
        if kFeatures != None:
            for feature in kFeatures:
                downloadParse(feature["id"], feature["name"], outputDir)
    return


def mergeAll(jsonAPIs, inputDir, mergedDir):
    """Merge per API and for all APIs"""
    # Load APIs json file
    with open(jsonAPIs) as f:
        apis = json.load(f)
    dfapis = []
    for api in apis["apis"]:
        dfs = []
        kFeatures = api["kFeatures"]
        # do not do anything if null
        if kFeatures != None:
            for feature in kFeatures:
                # get json data
                df = pd.read_json(inputDir + str(feature["id"]) + ".json")
                if not (df.empty):
                    df["day_percentage"] *= 100
                    # add feature name
                    df["feature"] = feature["name"]
                    dfs.append(df)

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
    """Plot the different graphs related to telemetry data from chromestatus, this function assumes that files have already been downloaded and merged"""
    # set sns style
    sns.set_style("whitegrid")
    with open(jsonAPIs) as f:
        apis = json.load(f)

    for api in apis["apis"]:
        if api["kFeatures"] == None:
            continue
        nColumns = api["plotOptions"]["nColumns"]
        figSize = [api["plotOptions"]["sizeX"], api["plotOptions"]["sizeY"]]

        # get the dataframe
        df = pd.read_csv(
            mergedDir + normalizeAPINames(api["name"]) + ".tsv",
            sep="\t",
            parse_dates=["date"],
        )
        # keep only data before endDate and aggregate following sampleRule
        df = (
            df[df["date"] < np.datetime64(endDate)]
            .groupby(["feature"])
            .resample(sampleRule, on="date")
            .mean()
            .reset_index()
        )
        # clip data below threshold to avoid weird artifacts on log graph
        df["day_percentage"] = df["day_percentage"].clip(lower=clipLower)

        # sort first by date (otherwise when we convert date to quarter and back to string, things are sometimes out of order)
        df = df.sort_values(["date"])
        dateMin = df["date"].min()
        dateMax = df["date"].max()
        df["date"] = df["date"].dt.to_period("Q").astype("string")

        plot = sns.lineplot(
            data=df,
            x="date",
            y="day_percentage",
            hue="feature",
            hue_order=np.sort(df["feature"].unique()),
            palette=glasbey.create_palette(
                palette_size=df["feature"].nunique(),
                colorblind_safe=True,
                optimize_palette_search_radius=50,
            ),  # type: ignore
            markers=True,
            style="feature",
            dashes=False,
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
            title="Feature",
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
    mergedDir,
    figsDir,
    endDate,
    logScale,
    sampleRule,
    clipLower,
    addDates,
    excludeDeprecatedAPIs,
):
    """Plot the upper envolope for each API from telemetry page loads, this function assumes that files have already been downloaded and merged"""
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
    df = df.groupby(["api", "date"])["day_percentage"].max().reset_index()
    # keep only data before endDate and aggregate following sampleRule
    df = (
        df[df["date"] < np.datetime64(endDate)]
        .groupby(["api"])
        .resample(sampleRule, on="date")
        .mean()
        .reset_index()
    )
    # clip data below threshold to avoid weird artifacts on log graph
    df["day_percentage"] = df["day_percentage"].clip(lower=clipLower)

    # sort first by date (otherwise when we convert date to quarter and back to string, things are sometimes out of order)
    df = df.sort_values(["date"])
    dateMin = df["date"].min()
    dateMax = df["date"].max()
    df["date"] = df["date"].dt.to_period("Q").astype("string")

    plot = sns.lineplot(
        data=df,
        x="date",
        y="day_percentage",
        hue="api",
        hue_order=np.sort(df["api"].unique()),
        palette=glasbey.create_palette(
            palette_size=df["api"].nunique(),
            colorblind_safe=True,
            optimize_palette_search_radius=50,
        ),  # type: ignore
        markers=True,
        style="api",
        dashes=False,
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
        title="API",
        frameon=False,
    )

    if logScale:
        plt.yscale("log")
        lowercaseName = "all-apis-upper-envelope" + "-log"
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


def printUsage(apiNames, quarters, mergedDir, endDate, sampleRule):
    """Return max page load usage for specified quarters and APIs"""

    print("Usage of non-deprecated APIs in past quarters")

    for apiName in apiNames:
        df = pd.read_csv(
            mergedDir + normalizeAPINames(apiName) + ".tsv",
            sep="\t",
            parse_dates=["date"],
        )
        # max only
        df = df.groupby(["date"])["day_percentage"].max().reset_index()
        # resample per quarter
        df = (
            df[df["date"] < np.datetime64(endDate)]
            .resample(sampleRule, on="date")
            .mean()
            .reset_index()
        )
        # convert date to quarter string
        df = df.sort_values(["date"])
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
    # filter by endDate and remove extra
    df = df[df["date"] < np.datetime64(endDate)]
    df = df[df["api"] != "extra"]

    print("Nb features per API")
    print(df.groupby(["api"])["feature"].nunique())
    print("\n")

    print("Nb datapoints per API")
    print(df.groupby(["api"])["day_percentage"].count())
    print("\n")

    print("Nb unique days per API")
    print(df.groupby(["api"])["date"].nunique())
    print("\n")

    print("Min date per API")
    print(df.groupby(["api"])["date"].min())
    print("\n")

    print("Max date per API")
    print(df.groupby(["api"])["date"].max())
    print("\n")

    print("Total stats")
    print("Nb features: {}".format(df["feature"].nunique()))
    print("Nb data points total: {}".format(df["day_percentage"].count()))
    print("Nb unique days: {}".format(df["date"].nunique()))
    print("Min day: {}".format(df["date"].min()))
    print("Max day: {}".format(df["date"].max()))

    print("--Max usage per quarter--")
    # max only
    df = df.groupby(["api", "date"])["day_percentage"].max().reset_index()
    # resample per quarter
    df = (
        df[df["date"] < np.datetime64(endDate)]
        .groupby(["api"])
        .resample("QS", on="date")
        .mean()
        .reset_index()
    )

    print("Max percentage per API")
    print(df.groupby(["api"])["day_percentage"].max())
    print("\n")

    return


if __name__ == "__main__":
    # Create Argument Parser
    parser = argparse.ArgumentParser(
        prog="python3 telemetry.py",
        description="Download telemetry data from chrome status platform",
    )
    req_grp = parser.add_argument_group(title="Required arguments")
    req_grp.add_argument(
        "-type",
        "--type",
        help="Execution type: download apis, aggregate",
        choices=["download", "merge", "plotAll", "plotMax", "stats"],
        required=True,
    )
    parser.add_argument(
        "-jsonAPIs",
        "--jsonAPIs",
        help="APIs input json file",
        default="./apis.json",
    )
    parser.add_argument(
        "-outputDir",
        "--outputDir",
        help="Output Directory",
        default="./data/telemetry/raw/",
    )
    parser.add_argument(
        "-mergedDir",
        "--mergedDir",
        help="Merged Directory",
        default="./data/telemetry/merged/",
    )
    parser.add_argument(
        "-figsDir",
        "--figsDir",
        help="Figs Directory",
        default="./figs/telemetry/",
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

    import json
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
        os.makedirs(os.path.dirname(args.outputDir), exist_ok=True)
        os.makedirs(os.path.dirname(args.mergedDir), exist_ok=True)
        os.makedirs(os.path.dirname(args.figsDir), exist_ok=True)

        if args.type == "download":
            downloadAll(args.jsonAPIs, args.outputDir)

        elif args.type == "merge":
            import pandas as pd

            mergeAll(args.jsonAPIs, args.outputDir, args.mergedDir)

        elif args.type == "plotAll":
            import glasbey
            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            import seaborn as sns

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

        elif args.type == "plotMax":
            import glasbey
            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            import seaborn as sns

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
                args.endDate,
            )
