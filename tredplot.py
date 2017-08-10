#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Copyright (c) 2015-2017 Human Longevity Inc.

Author: Haibao Tang <htang@humanlongevity.com>
License: Non-Commercial Use Only. For details, see `LICENSE` file

Related scripts for the HLI-STR (TREDPARSE) paper.
"""

import os.path as op
import sys
import json
import logging
import numpy as np

from tredparse.jcvi import FancyArrow, normalize_axes, panel_labels, plt, \
            savefig, OptionParser, ActionDispatcher


# Huntington risk allele
infected_thr = 40
ref_thr = 19
SIMULATED_HAPLOID = r'Simulated haploid $\mathit{h}$'
SIMULATED_DIPLOID = r"Simulated diploid $\mathit{20/h}$"
lsg = "lightslategray"


def main():

    actions = (
        # Plotting
        ('likelihood', 'plot likelihood surface and marginals'),
        ('likelihood2', 'plot likelihood surface and marginals for two settings'),
        # Diagram
        ('diagram', 'plot the predictive power of various evidences'),
            )
    p = ActionDispatcher(actions)
    p.dispatch(globals())


def mask_upper_triangle(data):
    mask = np.zeros_like(data)
    mask[np.triu_indices_from(mask)] = True
    data = np.ma.array(data, mask=mask)
    return data


def ax_plot(ax, P_h, h_hat, CI_h, xlabel, ylabel, ticks=True):
    max_P = max(P_h.values())
    a, b = CI_h

    ax.plot([h_hat, h_hat], [0, max_P], ":", color=lsg, lw=2)
    ax.set_xlabel(r"$%s$" % xlabel)
    ax.set_ylabel(ylabel)

    data = []
    for k in xrange(301):
        v = P_h.get(str(k), 0)
        data.append((k, v))
    data.sort()
    x, y = zip(*data)
    x = np.array(x)
    curve, = ax.plot(x, y, "-", color=lsg, lw=2)
    title = "Marginal distribution for $%s$" % xlabel
    ax.set_title(title)
    if not ticks:
        ax.set_yticks([])

    if a == b:
        ax.plot([h_hat, h_hat], [0, max_P], "-", color=lsg, lw=2)
    else:
        ax.fill_between(x, [0] * len(x), y, where=(x >= a) & (x <= b),
                         color=lsg, alpha=.5)
    ax.set_xlim(0, 300)

    ymin, ymax = ax.get_ylim()
    if h_hat < 150:
        ax.text(h_hat + 20, ymax * 4. / 5, r"$\hat{%s}=%d$" % (xlabel, h_hat),
                color=lsg, va="center")
        ax.text(h_hat + 20, ymax * 3. / 5, "95$\%$ CI" + r"$=%s-%s$" % (a, b),
                color=lsg, va="center")
    else:
        ax.text(h_hat - 30, ymax * 4. / 5, r"$\hat{%s}=%d$" % (xlabel, h_hat),
                color=lsg, ha="right", va="center")
        ax.text(h_hat - 30, ymax * 3. / 5, "95$\%$ CI" + r"$=%s-%s$" % (a, b),
                color=lsg, ha="right", va="center")

    ymin, ymax = ax.get_ylim()
    ax.set_ylim(ymin, ymax * 1.05)


def ax_imshow(ax, P_h1h2, cmap, label, h1_hat, h2_hat, samplekey,
              r=4, draw_circle=True, ticks=True):
    im = ax.imshow(P_h1h2, cmap=cmap, origin="lower")

    from mpl_toolkits.axes_grid1 import make_axes_locatable
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=.05)
    cb = plt.colorbar(im, cax)
    cb.set_label(label)
    if not ticks:
        cb.set_ticks([])

    if draw_circle:
        circle = plt.Circle((h1_hat, h2_hat), r, ec='w', fill=False)
        ax.add_artist(circle)

    annotation = "$\hat{h_1}=%d, \hat{h_2}=%d$" % (h1_hat, h2_hat)
    ax.text(200, 100, annotation, color=lsg, ha="center", va="center")

    ax.set_xlabel(r"$h_1$")
    ax.set_ylabel(r"$h_2$")
    title = "Joint probability density for $h_1$ and $h_2$ ({})"\
            .format(samplekey)
    ax.set_title(title)


def likelihood(args):
    """
    %prog likelihood 100_20.json

    Plot the likelihood surface and marginal distributions.
    """
    from matplotlib import gridspec

    p = OptionParser(likelihood.__doc__)
    p.add_option("--tred", default="HD",
                 help="TRED name to extract")
    opts, args, iopts = p.set_image_options(args, figsize="10x5",
                                style="white", cmap="coolwarm")

    if len(args) != 1:
        sys.exit(not p.print_help())

    jsonfile, = args
    fig = plt.figure(figsize=(iopts.w, iopts.h))
    gs = gridspec.GridSpec(2, 2)
    ax1 = fig.add_subplot(gs[:, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 1])
    plt.tight_layout(pad=3)
    pf = plot_panel(jsonfile, ax1, ax2, ax3, opts.cmap, tred=opts.tred)
    if not pf:
        logging.error("NO data found in P_h1h2. Plotting aborted.")
        return

    root = fig.add_axes([0, 0, 1, 1])
    normalize_axes(root)

    image_name = "likelihood.{}.".format(pf) + iopts.format
    savefig(image_name, dpi=iopts.dpi, iopts=iopts)


def likelihood2(args):
    """
    %prog likelihood2 200_20.json 200_100.json

    Plot the likelihood surface and marginal distributions for two settings.
    """
    from matplotlib import gridspec

    p = OptionParser(likelihood2.__doc__)
    p.add_option("--tred", default="HD",
                 help="TRED name to extract")
    opts, args, iopts = p.set_image_options(args, figsize="10x10",
                                style="white", cmap="coolwarm")
    if len(args) != 2:
        sys.exit(not p.print_help())

    jsonfile1, jsonfile2 = args
    fig = plt.figure(figsize=(iopts.w, iopts.h))
    gs = gridspec.GridSpec(9, 2)
    ax1 = fig.add_subplot(gs[:4, 0])
    ax2 = fig.add_subplot(gs[:2, 1])
    ax3 = fig.add_subplot(gs[2:4, 1])
    ax4 = fig.add_subplot(gs[5:, 0])
    ax5 = fig.add_subplot(gs[5:7, 1])
    ax6 = fig.add_subplot(gs[7:, 1])
    plt.tight_layout(pad=2)

    plot_panel(jsonfile1, ax1, ax2, ax3, opts.cmap, tred=opts.tred)
    plot_panel(jsonfile2, ax4, ax5, ax6, opts.cmap, tred=opts.tred)

    root = fig.add_axes([0, 0, 1, 1])
    pad = .02
    panel_labels(root, ((pad, 1 - pad, "A"), (pad, 4. / 9, "B")))
    normalize_axes(root)

    image_name = "likelihood2." + iopts.format
    savefig(image_name, dpi=iopts.dpi, iopts=iopts)


def plot_panel(jsonfile, ax1, ax2, ax3, cmap, tred='toy'):
    j = json.load(open(jsonfile))
    calls = j["tredCalls"]
    P_h1h2 = calls[tred + ".P_h1h2"]
    if not P_h1h2:
        return

    data = np.zeros((301, 301))
    data = mask_upper_triangle(data)
    for k, v in P_h1h2.items():
        a, b = k.split(",")
        a, b = int(a), int(b)
        if a < b:
            a, b = b, a
        data[a, b] = v

    label = "Probability density"
    h1_hat, h2_hat = calls[tred + ".1"], calls[tred + ".2"]
    pf = op.basename(jsonfile).split(".")[0]
    ax_imshow(ax1, data, cmap, label, h1_hat, h2_hat, pf,
              draw_circle=False, ticks=False)

    CI = calls[tred + ".CI"]
    CI_h1, CI_h2 = CI.split("|")
    CI_h1 = [int(x) for x in CI_h1.split('-')]
    CI_h2 = [int(x) for x in CI_h2.split('-')]
    P_h1 = calls[tred + ".P_h1"]
    P_h2 = calls[tred + ".P_h2"]

    ax_plot(ax2, P_h1, h1_hat, CI_h1, "h_1", label, ticks=False)
    ax_plot(ax3, P_h2, h2_hat, CI_h2, "h_2", label, ticks=False)

    return pf


def diagram(args):
    """
    %prog diagram

    Plot the predictive power of various evidences.
    """
    p = OptionParser(diagram.__doc__)
    opts, args, iopts = p.set_image_options(args, figsize="8x4", format="png")

    if len(args) != 0:
        sys.exit(not p.print_help())

    fig = plt.figure(1, (iopts.w, iopts.h))
    root = fig.add_axes([0, 0, 1, 1])

    # Gauge on top, this is log-scale
    yy = .7
    yinterval = .1
    height = .05
    yp = yy - yinterval - height
    canvas = .95
    xstart = .025
    convert = lambda x: xstart + x * canvas / 600
    # Symbols
    root.text(.5, .9, r"$L$: Read length, $F$: Flank size, $V$: Pair distance", ha="center")
    root.text(.5, .85, r"ex. $L=150bp, F=9bp, V=500bp$", ha="center")
    root.text(xstart + canvas, yy - height, "STR repeat length", ha="center",
              color=lsg, size=10)

    # Mark the key events
    pad = .02
    arrowlen = canvas * 1.05
    arrowprops = dict(length_includes_head=True, width=.01, fc=lsg, lw=0,
                      head_length=arrowlen * .12, head_width=.04)
    p = FancyArrow(xstart, yy, arrowlen, 0, shape="right", **arrowprops)
    root.add_patch(p)

    ppad = 30
    keyevents = ((       0,               0, -1, r"$0$"),
                 (150 - 18, 150 - 18 - ppad, 0, r"$L - 2F$"),
                  (150 - 9,         150 - 9, 1, r"$L - F$"),
                      (150,      150 + ppad, 2, r"$L$"),
                  (500 - 9,         500 - 9, 3, r"$V - F$"),
                )
    for event, pos, i, label in keyevents:
        _event = convert(event)
        _pos = convert(pos)
        root.plot((_event, _event), (yy - height / 4, yy + height / 4),
                  '-', color='k')
        root.text(_pos, yy + pad, label, rotation=45, va="bottom", size=8)
        if i < 0:
            continue
        ystart = yp - i * yinterval
        root.plot((_event, _event), (ystart, yy - height / 4), ':', color=lsg)

    # Range on bottom. These are simple 4 rectangles, with the range indicating
    # the predictive range.
    CLOSED, OPEN = range(2)
    ranges = ((0,       150 - 18, CLOSED, "Spanning reads"),
              (9,        150 - 9, OPEN,   "Partial reads"),
              (150,      500 - 9, CLOSED, "Repeat reads"),
              (0,        500 - 9, CLOSED, "Paired-end reads"),
             )
    for start, end, starttag, label in ranges:
        _start = convert(start)
        _end = convert(end)
        data = [[0., 1.], [0., 1.]] if starttag == OPEN else \
               [[1., 0.], [1., 0.]]
        root.imshow(data, interpolation='bicubic', cmap=plt.cm.Greens,
                    extent=[_start, _end, yp, yp + height])
        root.text(_end + pad, yp + height / 2, label, va="center")
        yp -= yinterval

    normalize_axes(root)

    image_name = "diagram." + iopts.format
    savefig(image_name, dpi=iopts.dpi, iopts=iopts)


if __name__ == '__main__':
    main()
