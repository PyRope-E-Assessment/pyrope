
import io

import matplotlib.tri
import matplotlib.pyplot as pp
import numpy as np


def logo(size=512, seed=42):

    np.random.seed(seed)

    # ratio of the circumradii of an octahedron and the quadrilateral
    # obtained by prolonging every second edge
    q = np.sqrt(2 - np.sqrt(2))

    # polar vertex coordinates
    R = 1/np.sqrt(2)
    r = np.array([0, R*q, R, R/q, 1, 1], ndmin=2).T
    phi = np.linspace(0, 2*np.pi, num=9)
    dphi = np.pi/8 * np.array(3*[0, 1], ndmin=2).T

    # cartesian vertex coordinates
    x = (r * np.cos(phi - dphi)).flatten()[7:]
    y = (r * np.sin(phi - dphi)).flatten()[7:]

    # Delaunay triangulation
    D = matplotlib.tri.Triangulation(x, y)

    # triangle centers
    Cx, Cy = np.mean([x[D.triangles], y[D.triangles]], axis=-1)

    # polar coordinates of triangle centers
    phi = np.arctan2(Cy, Cx)
    r = np.sqrt(Cx**2 + Cy**2) + phi/2**7

    # order triangles
    triangles = D.triangles[np.lexsort((phi, r))]

    # reorder triangles
    for i in (16, 32, 48):
        triangles[i:i+8], triangles[i+8:i+16] = (
            triangles[i+0:i+16:2].copy(),
            triangles[i+1:i+16:2].copy()
        )

    # triangulation with reordered triangles
    T = matplotlib.tri.Triangulation(x, y, triangles)

    # triangle colours
    TC = np.random.random(size=(8, 8))

    # inner octogon
    TC[0] = 1/3

    # equal colours for triangles forming a quadrilateral
    TC[[3, 6, 7]] = TC[[2, 4, 5]]

    TC = TC.flatten()

    # sparkling triangles
    S = matplotlib.tri.Triangulation(x, y, triangles[8:16])

    # sparkle colours
    SC = np.random.rand(8)

    # create figure
    pp.figure(figsize=(1, 1))
    pp.axis('off')
    pp.xlim(-1, +1)
    pp.ylim(-1, +1)
    pp.tripcolor(T, facecolors=TC, vmin=+0.0, vmax=3.0, cmap='hot')
    pp.tripcolor(S, facecolors=SC, vmin=-1.0, vmax=1.0, cmap='bone')

    # convert figure to image
    with io.BytesIO() as iobuffer:
        pp.savefig(iobuffer, transparent=True, dpi=size)
        iobuffer.seek(0)
        image = pp.imread(iobuffer)

    # prevent plotting
    pp.close()

    return image
