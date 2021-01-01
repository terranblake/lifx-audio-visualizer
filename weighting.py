#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Translated from a MATLAB script (which also includes C-weighting, octave
and one-third-octave digital filters).
Author: Christophe Couvreur, Faculte Polytechnique de Mons (Belgium)
        couvreur@thor.fpms.ac.be
Last modification: Aug. 20, 1997, 10:00am.
BSD license
http://www.mathworks.com/matlabcentral/fileexchange/69
Translated from adsgn.m to Python 2009-07-14 endolith@gmail.com
"""

from numpy import pi, polymul, logspace, log10
import numpy as np
from scipy.signal import zpk2tf, zpk2sos, freqs, sosfilt
import scipy


def filter_using_weights(b, a, x):
    return scipy.signal.lfilter(b, a, x).astype(int)


def _relative_degree(z, p):
    """
    Return relative degree of transfer function from zeros and poles
    """
    degree = len(p) - len(z)
    if degree < 0:
        raise ValueError("Improper transfer function. "
                         "Must have at least as many poles as zeros.")
    else:
        return degree


def _zpkbilinear(z, p, k, fs):
    """
    Return a digital filter from an analog one using a bilinear transform.
    Transform a set of poles and zeros from the analog s-plane to the digital
    z-plane using Tustin's method, which substitutes ``(z-1) / (z+1)`` for
    ``s``, maintaining the shape of the frequency response.
    Parameters
    ----------
    z : array_like
        Zeros of the analog IIR filter transfer function.
    p : array_like
        Poles of the analog IIR filter transfer function.
    k : float
        System gain of the analog IIR filter transfer function.
    fs : float
        Sample rate, as ordinary frequency (e.g. hertz). No prewarping is
        done in this function.
    Returns
    -------
    z : ndarray
        Zeros of the transformed digital filter transfer function.
    p : ndarray
        Poles of the transformed digital filter transfer function.
    k : float
        System gain of the transformed digital filter.
    """
    z = np.atleast_1d(z)
    p = np.atleast_1d(p)

    degree = _relative_degree(z, p)

    fs2 = 2.0 * fs

    # Bilinear transform the poles and zeros
    z_z = (fs2 + z) / (fs2 - z)
    p_z = (fs2 + p) / (fs2 - p)

    # Any zeros that were at infinity get moved to the Nyquist frequency
    z_z = np.append(z_z, -np.ones(degree))

    # Compensate for gain change
    k_z = k * np.real(np.prod(fs2 - z) / np.prod(fs2 - p))

    return z_z, p_z, k_z


def ABC_weighting(curve='A'):
    """
    Design of an analog weighting filter with A, B, or C curve.
    Returns zeros, poles, gain of the filter.
    Examples
    --------
    Plot all 3 curves:
    >>> from scipy import signal
    >>> import matplotlib.pyplot as plt
    >>> for curve in ['A', 'B', 'C']:
    ...     z, p, k = ABC_weighting(curve)
    ...     w = 2*pi*logspace(log10(10), log10(100000), 1000)
    ...     w, h = signal.freqs_zpk(z, p, k, w)
    ...     plt.semilogx(w/(2*pi), 20*np.log10(h), label=curve)
    >>> plt.title('Frequency response')
    >>> plt.xlabel('Frequency [Hz]')
    >>> plt.ylabel('Amplitude [dB]')
    >>> plt.ylim(-50, 20)
    >>> plt.grid(True, color='0.7', linestyle='-', which='major', axis='both')
    >>> plt.grid(True, color='0.9', linestyle='-', which='minor', axis='both')
    >>> plt.legend()
    >>> plt.show()
    """
    if curve not in 'ABC':
        raise ValueError('Curve type not understood')

    # ANSI S1.4-1983 C weighting
    #    2 poles on the real axis at "20.6 Hz" HPF
    #    2 poles on the real axis at "12.2 kHz" LPF
    #    -3 dB down points at "10^1.5 (or 31.62) Hz"
    #                         "10^3.9 (or 7943) Hz"
    #
    # IEC 61672 specifies "10^1.5 Hz" and "10^3.9 Hz" points and formulas for
    # derivation.  See _derive_coefficients()

    z = [0, 0]
    p = [
        -2 * pi * 20.598997057568145, -2 * pi * 20.598997057568145,
        -2 * pi * 12194.21714799801, -2 * pi * 12194.21714799801
    ]
    k = 1

    if curve == 'A':
        # ANSI S1.4-1983 A weighting =
        #    Same as C weighting +
        #    2 poles on real axis at "107.7 and 737.9 Hz"
        #
        # IEC 61672 specifies cutoff of "10^2.45 Hz" and formulas for
        # derivation.  See _derive_coefficients()

        p.append(-2 * pi * 107.65264864304628)
        p.append(-2 * pi * 737.8622307362899)
        z.append(0)
        z.append(0)

    elif curve == 'B':
        # ANSI S1.4-1983 B weighting
        #    Same as C weighting +
        #    1 pole on real axis at "10^2.2 (or 158.5) Hz"

        p.append(-2 * pi * 10**2.2)  # exact
        z.append(0)

    # TODO: Calculate actual constants for this
    # Normalize to 0 dB at 1 kHz for all curves
    b, a = zpk2tf(z, p, k)
    k /= abs(freqs(b, a, [2 * pi * 1000])[1][0])

    return np.array(z), np.array(p), k


def A_weighting(fs, output='ba'):
    """
    Design of a digital A-weighting filter.
    Designs a digital A-weighting filter for
    sampling frequency `fs`.
    Warning: fs should normally be higher than 20 kHz. For example,
    fs = 48000 yields a class 1-compliant filter.
    Parameters
    ----------
    fs : float
        Sampling frequency
    output : {'ba', 'zpk', 'sos'}, optional
        Type of output:  numerator/denominator ('ba'), pole-zero ('zpk'), or
        second-order sections ('sos'). Default is 'ba'.
    Examples
    --------
    Plot frequency response
    >>> from scipy.signal import freqz
    >>> import matplotlib.pyplot as plt
    >>> fs = 200000
    >>> b, a = A_weighting(fs)
    >>> f = np.logspace(np.log10(10), np.log10(fs/2), 1000)
    >>> w = 2*pi * f / fs
    >>> w, h = freqz(b, a, w)
    >>> plt.semilogx(w*fs/(2*pi), 20*np.log10(abs(h)))
    >>> plt.grid(True, color='0.7', linestyle='-', which='both', axis='both')
    >>> plt.axis([10, 100e3, -50, 20])
    Since this uses the bilinear transform, frequency response around fs/2 will
    be inaccurate at lower sampling rates.
    """
    z, p, k = ABC_weighting('A')

    # Use the bilinear transformation to get the digital filter.
    z_d, p_d, k_d = _zpkbilinear(z, p, k, fs)

    if output == 'zpk':
        return z_d, p_d, k_d
    elif output in {'ba', 'tf'}:
        return zpk2tf(z_d, p_d, k_d)
    elif output == 'sos':
        return zpk2sos(z_d, p_d, k_d)
    else:
        raise ValueError("'%s' is not a valid output form." % output)


def A_weight(signal, fs):
    """
    Return the given signal after passing through a digital A-weighting filter
    signal : array_like
        Input signal, with time as dimension
    fs : float
        Sampling frequency
    """
    # TODO: Upsample signal high enough that filter response meets Type 0
    # limits.  A passes if fs >= 260 kHz, but not at typical audio sample
    # rates. So upsample 48 kHz by 6 times to get an accurate measurement?
    # TODO: Also this could just be a measurement function that doesn't
    # save the whole filtered waveform.
    sos = A_weighting(fs, output='sos')
    return sosfilt(sos, signal).astype(int)


# if __name__ == "__main__":
#     import matplotlib.pyplot as plt
#     weighted_result = A_weight(np.ones(10000), 48000)
#     print('weights', weighted_result)
#     plt.plot(weighted_result)
#     plt.show()