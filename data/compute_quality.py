#!/usr/bin/env python3
import argparse
import os.path as path
import libquality.ffmpeg as ffmpeg
import libquality.quality as quality
import libquality.reference as reference
import libquality.profile as profile


def main():
    mods = profile.load("profiles")
    profiles = []
    for a in mods:
        if hasattr(mods[a], "Profile"):
            profiles.append(mods[a].Profile())

    profilenames = [profile.name for profile in profiles]
    basedir = path.dirname(path.realpath(__file__))
    env = {
        "scoredir": path.join(basedir, "scores"),
        "refdir": path.join(basedir, "references"),
        "tmpdir": path.join(basedir, "tmp"),
        "plotdir": path.join(basedir, "plots"),
    }

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", "--task", choices=["all", "transcode", "plot"],
        help="do only some of the tasks", default="all")
    parser.add_argument(
        "-p", "--profile", nargs="*", choices=profilenames,
        default=["voc-streaming"], help="only to testing for some comparison profile/s")
    parser.add_argument(
        "-s", "--source", default=path.join(basedir, "sources.json"),
        help="source description file")
    parser.add_argument(
        "tag", help="tag to identify your current testing platform")

    args = parser.parse_args()

    print("Comparison Profiles:", args.profile)

    profs = []
    for name in args.profile:
        profs.append(next(p for p in profiles if p.name == name))

    # transcode creates subformats and calculates scores, speed and actual rate
    if args.task == "all" or args.task == "transcode":

        # download/prepare reference files
        references = reference.ensure_references(args.source, env)
        print("Reference videos:", references)

        # compute scores
        quality.compare(references, profs, args.tag, env)

    # do plots
    if args.task == "all" or args.task == "plot":
        quality.plot(profs, env)

if __name__ == "__main__":
    main()