from random import sample
import numpy as np
import matplotlib.pyplot as plt


def plot(xy,
         r=1,
         c=1,
         i=1,
         title="",
         xlabel="",
         ylabel="",
         yticks=None,
         xticks=None,
         **plot_kwargs):
    plt.subplot(r, c, i)
    plt.title(title)
    if len(xy) == 2:
        plt.plot(*xy, **plot_kwargs)
    else:
        plt.plot(xy, **plot_kwargs)

    if xticks is not None:
        plt.xticks(xticks)
    if yticks is not None:
        plt.yticks(yticks)

    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    # plt.show()


def plot_fft(wave, fslice, sample_rate):
    X = np.fft.fft(wave)
    X_mag = np.abs(X)
    x = np.linspace(0, sample_rate, len(wave))
    y = X_mag * 2 / sample_rate

    return x[fslice], y[fslice]
