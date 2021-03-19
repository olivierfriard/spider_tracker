"""
spider coordinates analysis
2021 - Olivier Friard

the input file must be TSV (tab separated values)

Usage:
python3 coordinates_analysis_and_plot.py INPUT_FILE.tsv

"""

import sys
import pandas as pd
import pathlib as pl
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import kde
import scipy.signal

smoothing_window = 11

experiments = [x.strip().split("\t") for x in open(sys.argv[1], "r").readlines()]

coord_files_list = pl.Path("coordinates").glob("*.txt")

nbins = 100

for coord_file_path in sorted(coord_files_list):
    for exp in experiments:
        if coord_file_path.with_suffix('').name == exp[0]:
            resolution = exp[2]
            mm_px = exp[4]
            break
    else:
        print("not found")    
        break

    print(resolution, mm_px)
    mm_conv = float(mm_px.replace(",", "."))

    if resolution == "1280x720":
        x_lim = (0, 1280 * mm_conv)
        y_lim = (0, 720 * mm_conv)
    elif resolution == "1920x1080":
        x_lim = (0, 1920 * mm_conv)
        y_lim = (0, 1080 * mm_conv)
    else:
        print("resolution not found")
        sys.exit()

    df = pd.read_csv(coord_file_path, sep='\t', names=["frame", "x", "y"])
    print(coord_file_path.with_suffix('').name)

    df[f"x"] *= mm_conv
    df[f"y"] *= mm_conv

    dx = df[f"x"] - df[f"x"].shift(1)
    dy = df[f"y"] - df[f"y"].shift(1)
    dist = np.sqrt(dx**2 + dy**2)

    df['speed'] = dist
    df['cum_dist'] = df['speed'].cumsum()

    df['smoothed_speed'] = scipy.signal.savgol_filter(df['speed'], smoothing_window, 1)
    df['cum_dist_smoothed'] = df['smoothed_speed'].cumsum()


    d2x = dx - dx.shift(1)
    d2y = dy - dy.shift(1)
    df['acceleration'] = np.sqrt(d2x**2 + d2y**2)
    df['smoothed_acceleration'] = scipy.signal.savgol_filter(df['acceleration'], smoothing_window, 1)

    df['activity'] = (dist >= 5) * 1

    df.to_csv(coord_file_path.with_suffix(".df.csv"))

    #continue

    # plot speed
    plt.figure(figsize=(12, 12))
    axes = plt.gca()
    plt.xlabel("time")
    plt.ylabel("speed")
    plt.title(f"speed / time {coord_file_path.with_suffix('').name}")
    plt.plot(df["speed"])
    plt.tight_layout()
    plt.savefig(coord_file_path.with_suffix(".speed.svg"))
    plt.close()

    # plot speed    
    plt.figure(figsize=(12, 12))
    axes = plt.gca()
    plt.xlabel("time")
    plt.ylabel("smoothed speed")
    plt.title(f"smoothed speed / time {coord_file_path.with_suffix('').name}")
    plt.plot(df["smoothed_speed"])
    plt.tight_layout()
    plt.savefig(coord_file_path.with_suffix(".smoothed_speed.svg"))
    plt.close()

    # plot cumulative distance    
    plt.figure(figsize=(12, 12))
    axes = plt.gca()
    plt.xlabel("time")
    plt.ylabel("cumulative distance")
    plt.title(f"cumulative distance / time {coord_file_path.with_suffix('').name}")
    plt.plot(df["cum_dist"])
    plt.tight_layout()
    plt.savefig(coord_file_path.with_suffix(".cum_dist.svg"))
    plt.close()


    # path plot
    plt.figure(figsize=(12, 12))
    axes = plt.gca()
    axes.set_aspect("equal", adjustable="box")
    plt.xlabel("x")
    plt.ylabel("y")
    axes.set_xlim(x_lim)
    axes.set_ylim(y_lim)
    axes.set_ylim(axes.get_ylim()[::-1])
    plt.title(f"Path plot for {coord_file_path.with_suffix('').name}")
    plt.plot(df["x"], df["y"])
    plt.tight_layout()
    plt.savefig(coord_file_path.with_suffix(".path.svg"))
    plt.close()

    # density plot
    k = kde.gaussian_kde((df[f"x"].dropna(), df[f"y"].dropna()))

    xi, yi = np.mgrid[df[f"x"].dropna().min():df[f"x"].dropna().max():nbins*1j,
                      df[f"y"].dropna().min():df[f"y"].dropna().max():nbins*1j]
    zi = k(np.vstack([xi.flatten(), yi.flatten()]))

    plt.figure(figsize=(12, 12))
    axes = plt.gca()
    axes.set_aspect("equal", adjustable="box")

    plt.xlabel("x")
    plt.ylabel("y")

    axes.set_xlim(x_lim)
    axes.set_ylim(y_lim)
    axes.set_ylim(axes.get_ylim()[::-1])

    plt.title(f"Density plot for {coord_file_path.with_suffix('').name}")
    plt.pcolormesh(xi, yi, zi.reshape(xi.shape), shading="auto")  # , cmap=plt.cm.BuGn_r
    # plt.colorbar()
    plt.tight_layout()
    plt.savefig(coord_file_path.with_suffix(".density1.svg"))
    plt.close()
