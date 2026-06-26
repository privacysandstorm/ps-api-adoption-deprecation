import argparse


def parseAttestations(inputFile):
    """Parse one preloaded attestation file"""
    attestations = psa_pb2.PrivacySandboxAttestationsProto()  # type: ignore
    try:
        with open(inputFile, "rb") as f:
            attestations.ParseFromString(f.read())
    except IOError:
        exit(-1)

    origins = []
    apis = []
    allAPIsNames = []
    for api in attestations.all_apis:
        allAPIsNames.append(returnAPIName(api))

    for origin in attestations.sites_attested_for_all_apis:
        for api in allAPIsNames:
            origins.append(origin)
            apis.append(api)

    for origin, attestedAPIs in attestations.site_attestations.items():
        for api in attestedAPIs.attested_apis:
            origins.append(origin)
            apis.append(returnAPIName(api))

    df = pd.DataFrame({"origin": origins, "api": apis})
    return df


def mergeParseAttestations(inputDir, outputDir):
    """Parse pre-loaded attestations files and merge"""
    dfs = []

    for filename in os.listdir(inputDir):
        if os.path.isfile(os.path.join(inputDir, filename)):
            # format date correctly
            dateParts = filename.split(".")
            date = dateParts[0] + "-"
            if len(dateParts[1]) != 2:
                date += "0"
            date += dateParts[1] + "-"
            if len(dateParts[2]) != 2:
                date += "0"
            date += dateParts[2]
            # get attestation
            da = parseAttestations(os.path.join(inputDir, filename))
            da["date"] = date
            dfs.append(da)
    df = pd.concat(dfs)
    df.to_csv(os.path.join(outputDir, "attestations.tsv"), sep="\t", index=False)
    return


def returnAPIName(input):
    if input == UNKNOWN:
        print("unknown!")
        return None
    elif input == TOPICS:
        return "Topics"
    elif input == PROTECTED_AUDIENCE:
        return "Protected Audience"
    elif input == PRIVATE_AGGREGATION:
        return "Private Aggregation"
    elif input == ATTRIBUTION_REPORTING:
        return "Attribution Reporting"
    elif input == SHARED_STORAGE:
        return "Shared Storage"
    elif input == FENCED_STORAGE_READ:
        return "Fenced Storage Read"
    else:
        print("unknown!")
        return None


def returnCategory(category):
    if category == "Advertisements":
        return "Advertisements"
    elif category == "Information Technology":
        return "Information Technology"
    elif category == "Business and Economy":
        return "Business and Economy"
    elif category == "Web Hosting":
        return "Web Hosting"
    elif category == "Web Infrastructure":
        return "Web Infrastructure"
    elif category == "Web Analytics":
        return "Web Analytics"
    elif category == "Search Engines and Portals":
        return "Search Engines and Portals"
    elif category == "News and Media":
        return "News and Media"
    elif category == "Uncategorized":
        return "Unknown"
    else:
        return "Other"


def plotCategories(df, dc, figsDir):
    data = (
        df.merge(
            dc,
            left_on="origin",
            right_on="URL",
        )
        .groupby(["origin", "date"])["Category"]
        .first()
    ).reset_index()

    data["Category"] = data["Category"].apply(lambda x: returnCategory(x))

    # Data
    data = (
        data.groupby(["date", "Category"])["Category"].count().reset_index(name="count")
    )

    categories = np.sort(data["Category"].unique())
    dates = np.sort(data["date"].unique())
    y = np.zeros([len(categories), len(dates)])

    for i in range(len(dates)):
        result = data[data["date"] == dates[i]].sort_values("Category")["count"].values
        for j in range(len(result)):
            y[j][i] = result[j]

    # Plot
    plt.stackplot(
        dates,
        y,
        labels=categories,
    )
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Date")
    plt.ylabel("Count of origins")
    plt.legend(
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        title="Category",
        fontsize="small",
        ncol=1,
    )

    saveFig(os.path.join(figsDir, "categories.pdf"))

    return


def plotUpSet(df, dc, figsDir):
    from upsetplot import UpSet, from_indicators

    # crosstab on api column
    tab = (
        pd.crosstab([df["origin"], df["date"]], df["api"])
        .ne(0)
        .reset_index()
        .rename_axis(None, axis=1)
    )
    # filter to keep only last date for each origin
    data = tab.sort_values(by=["date"]).groupby(["origin"]).last()
    # merge categories
    data = data.merge(
        dc,
        left_on="origin",
        right_on="URL",
    )

    data["Category"] = data["Category"].apply(lambda x: returnCategory(x))

    upset = UpSet(
        from_indicators(
            [
                "Attribution Reporting",
                "Private Aggregation",
                "Protected Audience",
                "Shared Storage",
                "Topics",
            ],
            data=data,
        ),
        element_size=10,
        sort_by="cardinality",
        # orientation="vertical",
        intersection_plot_elements=0,
    )  # disable the default bar chart
    upset.add_stacked_bars(
        by="Category",
        colors=sns.color_palette("tab10"),
        title="Count by origin category",
        elements=10,
    )
    matplotlib.rcParams["font.size"] = 8

    upset.plot()
    saveFig(os.path.join(figsDir, "upset.pdf"), [6, 4])
    return


def plotFluctuations(df, figsDir):
    sns.set_style("whitegrid")
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1)

    data = df.groupby("date")["origin"].nunique().reset_index()
    sns.lineplot(data, x="date", y="origin", marker="o", ax=ax1)  # , label="Versions")
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)
    ax1.set(ylabel="Origins enrolled")
    ax1.set(xlabel="")

    # sort dates
    dates = np.sort(df["date"].unique())
    n = len(dates)
    removed = np.zeros(n - 1)
    added = np.zeros(n - 1)

    prior = set(df[df["date"] == dates[0]]["origin"].unique())
    for i in range(1, n):
        current = set(df[df["date"] == dates[i]]["origin"].unique())
        # removed origins
        removed[i - 1] = -len(prior.difference(current))
        # new origins
        added[i - 1] = +len(current.difference(prior))
        prior = current

    x = np.arange(1, n)
    sns.barplot(x=x, y=added, ax=ax2, label="Additions")
    sns.barplot(x=x, y=removed, ax=ax2, label="Removals")
    ax2.legend()
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set(ylabel="Fluctuations")
    ax2.set(xlabel="File version (228 origins in v0)")
    for label in ax2.get_xticklabels():
        if int(label.get_text()) % 5 == 0 or label.get_text() == "1":
            label.set_visible(True)
        else:
            label.set_visible(False)

    # x = mdates.date2num(dates[1:])
    # ax2.bar(x, added, width=5, color="#1f77b4", fill=True, label="Additions")
    # ax2.bar(x, removed, width=5, color="#ff7f0e", fill=True, label="Removals")
    # locator = mdates.AutoDateLocator()
    # formatter = mdates.ConciseDateFormatter(locator)
    # ax2.xaxis.set_major_locator(locator)
    # ax2.xaxis.set_major_formatter(formatter)
    # ax2.axhline(0, color="black", linewidth=0.8)
    # ax2.legend()
    # ax2.set(ylabel="Fluctuations in enrolled origins")

    saveFig(os.path.join(figsDir, "barplotFluctuations.pdf"))

    return


def plotAll(attestationsPath, categoriesPath, figsDir):

    df = pd.read_csv(
        attestationsPath,
        sep="\t",
        parse_dates=["date"],
    )

    dc = pd.read_csv(categoriesPath, sep="\t")

    plotUpSet(df, dc, figsDir)
    plotFluctuations(df, figsDir)
    plotCategories(df, dc, figsDir)

    return


if __name__ == "__main__":
    # Create Argument Parser
    parser = argparse.ArgumentParser(
        prog="python3 attestations.py",
        description="Parse and plot attestations files",
    )
    req_grp = parser.add_argument_group(title="Required arguments")
    req_grp.add_argument(
        "-type",
        "--type",
        help="Execution type: aggregate, plot",
        choices=["merge", "plot", "stats"],
        required=True,
    )
    parser.add_argument(
        "-inputDir",
        "--inputDir",
        help="Input Directory",
        default="./data/attestations/pre-loaded/",
    )
    parser.add_argument(
        "-outputDir",
        "--outputDir",
        help="Output Directory",
        default="./data/attestations/",
    )
    parser.add_argument(
        "-figsDir",
        "--figsDir",
        help="Figs Directory",
        default="./figs/attestations/",
    )
    args = parser.parse_args()

    import os

    from utils import (
        addVerticalDates,
        convertTicklabelsQuarters,
        normalizeAPINames,
        saveFig,
    )

    # Automatically create the output directory hierarchy if needed
    os.makedirs(os.path.dirname(args.outputDir), exist_ok=True)
    os.makedirs(os.path.dirname(args.figsDir), exist_ok=True)

    import pandas as pd
    import data.attestations.privacy_sandbox_attestations_pb2 as psa_pb2

    ## APIs definitions
    #   UNKNOWN = 0;
    #   TOPICS = 1;
    #   PROTECTED_AUDIENCE = 2;
    #   PRIVATE_AGGREGATION = 3;
    #   ATTRIBUTION_REPORTING = 4;
    #   SHARED_STORAGE = 5;
    #   FENCED_STORAGE_READ = 6;
    UNKNOWN = psa_pb2.PrivacySandboxAttestationsGatedAPIProto.UNKNOWN  # type: ignore
    TOPICS = psa_pb2.PrivacySandboxAttestationsGatedAPIProto.TOPICS  # type: ignore
    PROTECTED_AUDIENCE = (
        psa_pb2.PrivacySandboxAttestationsGatedAPIProto.PROTECTED_AUDIENCE  # type: ignore
    )
    PRIVATE_AGGREGATION = (
        psa_pb2.PrivacySandboxAttestationsGatedAPIProto.PRIVATE_AGGREGATION  # type: ignore
    )
    ATTRIBUTION_REPORTING = (
        psa_pb2.PrivacySandboxAttestationsGatedAPIProto.ATTRIBUTION_REPORTING  # type: ignore
    )
    SHARED_STORAGE = (
        psa_pb2.PrivacySandboxAttestationsGatedAPIProto.SHARED_STORAGE  # type: ignore
    )
    FENCED_STORAGE_READ = (
        psa_pb2.PrivacySandboxAttestationsGatedAPIProto.FENCED_STORAGE_READ  # type: ignore
    )

    if args.type == "merge":
        mergeParseAttestations(args.inputDir, args.outputDir)

    elif args.type == "plot":
        import matplotlib
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import numpy as np
        import seaborn as sns

        plotAll(
            os.path.join(args.outputDir, "attestations.tsv"),
            os.path.join(args.outputDir, "categories-threatseeker.tsv"),
            args.figsDir,
        )

    elif args.type == "stats":

        import numpy as np

        df = pd.read_csv(
            os.path.join(args.outputDir, "attestations.tsv"),
            sep="\t",
            parse_dates=["date"],
        )
        dc = pd.read_csv(
            os.path.join(args.outputDir, "categories-threatseeker.tsv"),
            sep="\t",
        )
        print("Unique origins: {}".format(df["origin"].nunique()))  # 295 unique origins
        print("Unique dates: {}".format(df["date"].nunique()))  # 29 dates
        print("From: {}".format(df["date"].min()))  #'2024-06-05'
        print("To: {}".format(df["date"].max()))  #'2025-07-18'
        print(
            "APIs: {}".format(df["api"].unique())
        )  # 5 apis only ['Attribution Reporting',   'Private Aggregation',    'Protected Audience',     'Shared Storage', 'Topics']

        # evolution over time of number of origins
        print(df.groupby(["date"])["origin"].nunique())

        # dw = pd.read_csv(
    #     "./well-known-crawler/attestation_known_apis.tsv",
    #     sep="\t",
    # )
    # 264 unique enrollment sites, 9 only with Android related APIs
    # missing 42 from Chrome file
    # diff = set(df["origin"].unique()).difference(set(dw["enrollment_site"].unique()))
    # pipe into missing-attestations.txt
    # for origin in diff:
    #     print(origin)
