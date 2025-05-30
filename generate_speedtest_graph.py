
import sys
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
from io import BytesIO
import base64
import os
import matplotlib.dates as mdates
import zoneinfo
import numpy as np

def main(filename, show_all=False, height_px=300, width_px=None, tz_override=None, max_mbps=None, last_hours=None):
    try:
        with open(filename, "r") as file:
            data = [json.loads(line) for line in file.readlines()]
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    records = []
    for entry in data:
        try:
            timestamp = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            download = entry["download"]["bandwidth"] * 8 / 1_000_000
            upload = entry["upload"]["bandwidth"] * 8 / 1_000_000
            ping = entry["ping"]["latency"]
            packet_loss = entry.get("packetLoss", 0)
            records.append({
                "timestamp": timestamp,
                "download_mbps": download,
                "upload_mbps": upload,
                "latency_ms": ping,
                "packet_loss_percent": packet_loss
            })
        except (KeyError, ValueError):
            continue

    df = pd.DataFrame(records)
    df = df.sort_values("timestamp")

    tz_name = tz_override or os.environ.get("TZ", "UTC")
    try:
        tzinfo = zoneinfo.ZoneInfo(tz_name)
        df["timestamp"] = df["timestamp"].dt.tz_convert(tzinfo)
    except Exception as e:
        print(f"Invalid TZ setting: {tz_name}", file=sys.stderr)
        sys.exit(1)

    now = pd.Timestamp.now(tzinfo)

    if last_hours:
        since = now - pd.Timedelta(hours=last_hours)
        df = df[df["timestamp"] >= since]
    elif not show_all:
        today = now.normalize()
        df = df[df["timestamp"].dt.normalize() == today]

    if df.empty:
        print("No data to plot", file=sys.stderr)
        sys.exit(1)

    fig_height_in = height_px / 100
    if width_px:
        fig_width_in = width_px / 100
        x_values = np.linspace(0, 1, len(df))
        x_labels = df["timestamp"]
        x_ticks = x_values
        # plt.subplots_adjust(left=0.06, right=2.97, top=0.88, bottom=0.2)
    else:
        fig_width_in = max(10, len(df) * 0.5)
        x_values = df["timestamp"]
        x_labels = None
        x_ticks = None
        # plt.tight_layout(pad=0)

    fig, ax1 = plt.subplots(figsize=(fig_width_in, fig_height_in))

    ax1.plot(x_values, df["download_mbps"], label="Download (Mbps)", marker='o')
    ax1.plot(x_values, df["upload_mbps"], label="Upload (Mbps)", marker='o')
    ax1.set_ylabel("Speed (Mbps)")
    ax1.set_xlabel("Time")
    ax1.tick_params(axis='x', rotation=45)
    ax1.set_ylim(bottom=0, top=max_mbps if max_mbps else None)

    ax2 = ax1.twinx()
    ax2.plot(x_values, df["latency_ms"], label="Latency (ms)", linestyle='--', marker='x', color='green')
    ax2.plot(x_values, df["packet_loss_percent"], label="Packet Loss (%)", linestyle='--', marker='x', color='red')
    ax2.set_ylabel("Latency / Packet Loss")
    ax2.set_ylim(bottom=0, top=df["latency_ms"].max())

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    all_lines = lines_1 + lines_2
    all_labels = labels_1 + labels_2

    fig.legend(
        all_lines, all_labels,
        loc='upper center',
        ncol=len(all_labels),
        bbox_to_anchor=(0.5, 0.995),
        bbox_transform=fig.transFigure
    )

    # Adjust margins to minimize whitespace around plot
    #plt.subplots_adjust(left=1.0, right=1.6, top=27.0, bottom=1.0)
    plt.tight_layout()

    if width_px:
        ax1.set_xticks(x_ticks)
        label_count = len(x_labels)
        max_labels = int(width_px / 80)
        if label_count > max_labels:
            interval = int(np.ceil(label_count / max_labels))
            visible_labels = [ts.strftime("%H:%M") if i % interval == 0 else "" for i, ts in enumerate(x_labels)]
        else:
            visible_labels = [ts.strftime("%H:%M") for ts in x_labels]
        ax1.set_xticklabels(visible_labels)
    else:
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=tzinfo))

    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=100)
    plt.close(fig)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("ascii")

    print(f"data:image/png;base64,{encoded}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate a speedtest graph.")
    parser.add_argument("json_file", help="Path to the speedtest JSON file")
    parser.add_argument("--all", action="store_true", help="Show all data, not just today")
    parser.add_argument("--height", type=int, default=300, help="Image height in pixels (default: 300)")
    parser.add_argument("--width", type=int, help="Image width in pixels (optional)")
    parser.add_argument("--max-mbps", type=float, help="Max value for speed y-axis (Mbps)")
    parser.add_argument("--last-hours", type=int, help="Only include data from the last X hours")
    parser.add_argument("--tz", type=str, help="Timezone name (e.g. Australia/Sydney)")
    args = parser.parse_args()

    main(
        args.json_file,
        show_all=args.all,
        height_px=args.height,
        width_px=args.width,
        tz_override=args.tz,
        max_mbps=args.max_mbps,
        last_hours=args.last_hours
    )
