import numpy as np


def create_rectangular_mask(roi_coords, data_slice):
    try:
        x1, y1, x2, y2 = map(int, map(np.floor, roi_coords))
        mask = create_empty_mask(data_slice)

        ix1, ix2 = sorted([int(x1), int(x2)])
        iy1, iy2 = sorted([int(y1), int(y2)])

        # Clip para no salirnos del array
        ix1, ix2 = np.clip([ix1, ix2], 0, data_slice.shape[0])
        iy1, iy2 = np.clip([iy1, iy2], 0, data_slice.shape[1])

        mask[ix1:ix2, iy1:iy2] = True

        return mask

    except Exception as e:
        print(f"Error procesando el ROI: {e}")


def create_elliptical_mask(roi_coords, ellipsis_center, radius, data_slice):
    x1, y1, x2, y2 = map(int, map(np.floor, roi_coords))

    ix1, ix2 = sorted([int(x1), int(x2)])
    iy1, iy2 = sorted([int(y1), int(y2)])

    ix1, ix2 = np.clip([ix1, ix2], 0, data_slice.shape[0])
    iy1, iy2 = np.clip([iy1, iy2], 0, data_slice.shape[1])

    xc, yc = ellipsis_center
    a, b = radius

    mask = create_empty_mask(data_slice)

    for y in range(iy1, iy2):
        for x in range(ix1, ix2):
            if ((x - xc) ** 2) / (a ** 2) + ((y - yc) ** 2) / (b ** 2) <= 1:
                mask[x, y] = True

    return mask


def create_empty_mask(data_slice):
    return np.zeros_like(data_slice, dtype=bool)
