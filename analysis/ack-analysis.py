import argparse
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import StrMethodFormatter

from collections import deque
from pathlib import Path
from glob import glob

BLUE = deque(['#0000FF', '#0000B3', '#0081B3',
              '#14293D', '#A7DFE2', '#8ED9CD'])
RED = deque(['#FF0000', '#950000', '#FF005A',
             '#A9385A', '#C95DB4', 'orange',
             '#FF0000', '#950000', ])
GREEN = deque(['#00FF00', '#008D00', '#005300',
               '#00FF72', '#76FF00', '#24A547',
               '#00FF00', '#008D00', ])
ORANGE = deque(['#FF8100', '#FFA700', '#FF6D26'])
YELLOW = deque(['#FFFF00', '#DCFF20', '#DCC05A'])
PURPLE = deque(['#6A00CD', '#A100CD', '#7653DE'])


def analyze_pcap(filename: str) -> (dict, str):
    print(filename)
    with open(filename) as f:
        data = json.load(f)

        ack_ts = {}
        received_ts = {}

        fin = False

        # Associate each ACK offset with a timestamp
        for packet in data:
            tcp = packet['_source']['layers']['tcp']
            srcport = tcp['tcp.srcport']
            dstport = tcp['tcp.dstport']
            time = float(tcp['Timestamps']['tcp.time_relative']) * 1000

            # receive packet
            if srcport == '443':
                if tcp['tcp.flags_tree']['tcp.flags.fin'] == '1':
                    fin = True
                bytes_ack = int(tcp['tcp.seq'])
                received_ts[time] = bytes_ack / 1024
            # send packet
            else:
                if fin:
                    continue
                if tcp['tcp.flags_tree']['tcp.flags.syn'] == '1' and time > 500:
                    fin = True
                    continue

                bytes_ack = int(tcp['tcp.ack'])
                ack_ts[time] = bytes_ack / 1024

    return ack_ts, filename


def analyze_qlog(filename: str) -> (dict, str):
    print(filename)
    with open(filename) as f:
        data = json.load(f)
        traces = data['traces'][0]
        events = traces['events']
        if 'configuration' in traces:
            time_units = traces['configuration']['time_units']
        else:
            time_units = 'ms'

        first_time = None

        ack_ts = {}
        pkts_received = {}
        received_ts = {}

        prev_pkt = {'pn': 0, 'dl': 0}
        loss_count = 0

        # Store all stream packets received by client
        for event in events:
            if not event:
                continue

            if time_units == 'ms':
                ts = int(event[0])
            else:
                ts = int(event[0]) / 1000

            event_type = event[2]
            event_data = event[3]

            if event_type.lower() == 'packet_sent' and first_time is None:
                first_time = ts

            if first_time is None:
                continue

            ts -= first_time

            if event_type.lower() == 'packet_received':

                # Associate packet num with data offset
                if 'frames' not in event_data:
                    continue

                frames = event_data['frames']

                for frame in frames:
                    if frame['frame_type'].lower() == 'stream':
                        if frame['stream_id'] != '0':
                            continue

                        pkt_num = int(event_data['header']['packet_number'])
                        offset = int(frame['offset'])
                        length = int(frame['length'])

                        data_length = (offset + length) / 1024

                        pkts_received[pkt_num] = data_length
                        received_ts[ts] = data_length

                        if prev_pkt['dl'] < data_length:
                            prev_pkt = {'pn': pkt_num, 'dl': data_length}
                        elif prev_pkt['pn'] < pkt_num:
                            # print('loss detected', prev_pkt, data_length)
                            loss_count += 1
                        else:
                            print('out of order packet')

            if event_type.lower() == 'packet_sent':
                # Get max ack sent
                if 'frames' not in event_data:
                    continue

                local_max_ack = None
                frames = event_data['frames']
                for frame in frames:
                    if 'acked_ranges' not in frame:
                        continue

                    for ack in frame['acked_ranges']:
                        if len(ack) != 2:
                            continue

                        ack_begin = int(ack[0])
                        ack_end = int(ack[1])

                        for i in range(ack_begin, ack_end + 1):
                            if i not in pkts_received:
                                continue

                            if local_max_ack is None:
                                local_max_ack = pkts_received[i]

                            local_max_ack = max(
                                local_max_ack, pkts_received[i])

                if local_max_ack is not None:
                    ack_ts[ts] = local_max_ack

    print(loss_count)
    return ack_ts, filename


def plot_ack(data, graph_title: str):
    fig, ax = plt.subplots(figsize=(8, 6))
    # plt.ylabel('Total KB ACKed')
    # plt.xlabel('Time (ms)')
    # plt.title(graph_title)

    legend = [
        mpatches.Patch(color='red', label='Chrome H3'),
        mpatches.Patch(color='blue', label='Proxygen H3'),
        mpatches.Patch(color='green', label='Ngtcp2 H3'),
        mpatches.Patch(color='orange', label='Quiche H3'),
        mpatches.Patch(color='yellow', label='Aioquic H3'),
    ]

    for i, (ack_ts, title) in enumerate(data):

        if title.count('.json') > 0:
            color = RED.popleft()
        elif title.count('chrome') > 0:
            color = BLUE.popleft()
        elif title.count('proxygen') > 0:
            # color = BLUE.popleft()
            color = 'green'
        elif title.count('ngtcp2') > 0:
            color = GREEN.popleft()
        elif title.count('quiche') > 0:
            color = PURPLE.popleft()
        elif title.count('aioquic') > 0:
            color = YELLOW.popleft()

        plt.plot(
            [x[0] for x in ack_ts.items()],
            [x[1] for x in ack_ts.items()],
            color=color,
            marker='o',
            linestyle='-',
            linewidth=1,
            markersize=4,
        )

    ax.tick_params(axis='both', which='major', labelsize=18)
    ax.tick_params(axis='both', which='minor', labelsize=18)

    formatter0 = StrMethodFormatter('{x:,g} kb')
    ax.yaxis.set_major_formatter(formatter0)

    formatter1 = StrMethodFormatter('{x:,g} ms')
    ax.xaxis.set_major_formatter(formatter1)

    # plt.yticks(np.array([0, 250, 500, 750, 1000]))
    # plt.xticks(np.array([1000, 3000, 5000, 7000]))
    plt.xticks(np.array([0, 300, 600, 900, 1200]))
    fig.tight_layout()
    plt.savefig(
        '{}/Desktop/graphs/{}'.format(Path.home(), graph_title), transparent=True)
    # plt.legend(handles=legend)
    plt.show()
    plt.close(fig=fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qlogdir")
    parser.add_argument("--pcapdir")

    args = parser.parse_args()

    qlogdir = args.qlogdir
    pcapdir = args.pcapdir

    data = []

    files = glob('{}/**/*.qlog'.format(qlogdir), recursive=True)
    files.sort()
    for qlog in files:
        if qlog.count('server') > 0:
            continue
        if qlog.count('proxygen') == 0:
            continue
        # if qlog.split('.')[0][-2:] not in ['n8', '20', '21']:
        #     continue

        data.append(analyze_qlog(qlog))
        print(qlog, max(data[-1][0].keys()))

    if pcapdir is not None:
        files = glob('{}/**/*.json'.format(pcapdir), recursive=True)
        for pcap in files:
            if pcap.split('.')[0][-1] > '3':
                continue
            data.append(analyze_pcap(pcap))
            print(pcap, max(data[-1][0].keys()))

    plot_ack(data, qlogdir.split('/')[-1])


if __name__ == "__main__":
    main()
