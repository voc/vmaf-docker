from os import path
from libquality.profile import Profile as Base


class Profile(Base):
    name = "tracker-vpx"
    dimensions = ["encoder", "setting"]

    def formats(self):
        yield {
            "encoder": "x264",
            "setting": "tracker",
            "opts": f"""
    -i $ref
    -c:v libx264
    -crf:v 23
    -maxrate:v 6000k -bufsize:v 12000k
    -profile:v high
    -level:v 4.1
    -disposition:v default
"""}

        yield {
            "encoder": "libvpx",
            "setting": "tracker",
            "opts": f"""
    -i $ref
    -c:v libvpx
    -threads:v 8
    -b:v 5000k -crf:v 23 -quality good -speed 2 -slices 4
"""}
        for speed in [4,5]: 
          yield {
                "encoder": "libvpx-vp9",
                "setting": f"rt{speed}",
                "opts": f"""
    -i $ref
    -c:v libvpx-vp9
    -quality:v realtime
    -crf:v 28
    -speed:v {speed}
    -b:v 6000k
    -maxrate:v 8000k
    -minrate:v 2000k
    -row-mt 1
    -frame-parallel:v 1 -tile-columns:v 2
"""}

        for crf in [28,29,30,31,32]:
            yield {
                "encoder": "libvpx-vp9",
                "setting": f"crf{crf}",
                "opts": f"""
    -i $ref
    -c:v libvpx-vp9
    -quality:v good
    -crf:v {crf}
    -b:v 6000k
    -maxrate:v 8000k
    -minrate:v 2000k
    -row-mt 1
    -frame-parallel:v 1 -tile-columns:v 2
"""}

    def plot(self, df, plotdir):
        self.plot_score_per_rate(df.copy(), plotdir)
        self.plot_score_per_ref(df.copy(), plotdir)
        self.plot_speeds(df.copy(), plotdir)

    def plot_score_per_rate(self, df, plotdir):
        import pandas as pd
        import matplotlib.pyplot as plt

        # label codecs
        df.loc[:, "label"] = df["encoder"] + "-" + df["setting"]

        # Group scores by target rate
        group = df.groupby(["setting", "label"])
        scores = group[["score_mean"]].mean().unstack().droplevel(0, axis=1)
        rates = group[["rate"]].mean().unstack().droplevel(0, axis=1)

        # But plot with real rate
        legend = []
        plt.rcParams["figure.figsize"] = (8, 6)
        for label in scores:
            data = pd.DataFrame({label: scores[label], "rate": rates[label]})
            plt.plot(data["rate"]/1000, data[label], "-+")
            legend.append(label)

        maxrate = group[["rate"]].max().reset_index(drop=True).max()[0] / 1000
        plt.axis([0, maxrate + 1, 0, 100])
        plt.legend(legend)
        plt.title("Score")
        plt.xlabel("Avg. Bitrate in Mbit/s")
        plt.ylabel("Mean VMAF score over all references")
        plt.title("Score over Bitrate")
        plt.grid(True)
        plt.savefig(path.join(plotdir, "tracker_rates.pdf"))
        plt.close()

    def plot_score_per_ref(self, df, plotdir):
        import matplotlib.pyplot as plt

        # label codecs
        df.loc[:, "label"] = df["encoder"] + "-" + df["setting"]

        group = df.groupby(["label", "reference"])
        scores = group[["score_mean"]].mean().unstack("label").droplevel(0, axis=1)
        errors = group[["score_mean"]].mad().unstack("label").droplevel(0, axis=1)

        plt.rcParams["figure.figsize"] = (8, 6)
        scores.plot.bar(ylim=(0, 100), yerr=errors, capsize=2)
        plt.title("Codec comparison per reference file")
        plt.ylabel("Mean VMAF score + MAD")
        plt.subplots_adjust(bottom=0.2)
        plt.grid(True)
        plt.savefig(path.join(plotdir, "tracker_references.pdf"))
        plt.close()

    def plot_speeds(self, df, plotdir):
        import pandas as pd
        import matplotlib.pyplot as plt

        # only show speed for vaapi codecs
        df.loc[:, "label"] = df["encoder"] + "-" + df["setting"]

        # Group scores by target rate
        group = df.groupby(["setting", "label"])
        speeds = group[["speed"]].mean().unstack().droplevel(0, axis=1)
        rates = group[["rate"]].mean().unstack().droplevel(0, axis=1)
        errors = group[["speed"]].mad().unstack().droplevel(0, axis=1)

        # But plot with real rate
        legend = []
        plt.rcParams["figure.figsize"] = (8, 6)
        for label in speeds:
            data = pd.DataFrame({label: speeds[label], "rate": rates[label]})
            plt.errorbar(data["rate"]/1000, data[label], yerr=errors[label], capsize=2)
            legend.append(label)

        plt.legend(legend)

        maxspeed = group[["speed"]].max().reset_index(drop=True).max()[0]
        maxrate = group[["rate"]].max().reset_index(drop=True).max()[0] / 1000
        plt.axis([0, maxrate + 1, 0, maxspeed + 1])
        plt.title("Coding Speed for vaapi/libvpx")
        plt.xlabel("Avg. Bitrate in Mbit/s")
        plt.ylabel("Encoding Speed in multiples of realtime")
        plt.title("Speed over Bitrate")
        plt.grid(True)
        plt.savefig(path.join(plotdir, "tracker_speeds.pdf"))
        plt.close()


# formats = EncodingFormats(dimensions, generate_formats())
# profile = Profile("voc-streaming", formats, )