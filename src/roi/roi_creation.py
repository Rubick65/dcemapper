import numpy as np
from scipy import ndimage
from skimage.draw import polygon
from skimage.transform import resize


def update_rectangular_mask(roi_coords, full_mask, z_index):
    try:

        new_selection = np.zeros(
            (full_mask.shape[0], full_mask.shape[1]),
            dtype=float
        )

        x1, y1, x2, y2 = map(int, map(np.floor, roi_coords))

        ix1, ix2 = sorted([x1, x2])
        iy1, iy2 = sorted([y1, y2])

        ix1, ix2 = np.clip([ix1, ix2], 0, full_mask.shape[0])
        iy1, iy2 = np.clip([iy1, iy2], 0, full_mask.shape[1])

        new_selection[ix1:ix2, iy1:iy2] = 1.0

        smooth_mask = ndimage.gaussian_filter(
            new_selection,
            sigma=0.5
        )

        smooth_mask = np.clip(smooth_mask, 0, 1)

        full_mask[:, :, z_index] = np.minimum(
            full_mask[:, :, z_index],
            smooth_mask
        )

        return full_mask

    except Exception as e:

        print(f"Error procesando el ROI: {e}")

        return full_mask


def update_elliptical_mask(full_mask, ellipsis_center, radius, z_index):
    try:

        xc, yc = ellipsis_center
        a, b = radius

        x = np.arange(full_mask.shape[0])
        y = np.arange(full_mask.shape[1])

        xv, yv = np.meshgrid(x, y, indexing='ij')

        ellipse = (
                ((xv - xc) ** 2) / (a ** 2) +
                ((yv - yc) ** 2) / (b ** 2)
        )

        mask = (ellipse <= 1).astype(float)

        # suavizado real
        smooth_mask = ndimage.gaussian_filter(
            mask,
            sigma=1.0
        )

        smooth_mask = np.clip(smooth_mask, 0, 1)

        full_mask[:, :, z_index] = np.minimum(
            full_mask[:, :, z_index],
            smooth_mask
        )

        return full_mask

    except Exception as e:

        print(f"Error en máscara elíptica: {e}")

        return full_mask


def update_polygon_mask(full_mask, polygon_coords, z_index):
    try:
        h, w = full_mask.shape[:2]
        factor = 4

        h_big, w_big = h * factor, w * factor
        coords_big = np.array(polygon_coords) * factor


        rr, cc = polygon(coords_big[:, 0], coords_big[:, 1], shape=(h_big, w_big))
        mask_big = np.zeros((h_big, w_big), dtype=float)
        mask_big[rr, cc] = 1.0

        smooth_mask = resize(mask_big, (h, w), order=1, anti_aliasing=True)

        full_mask[:, :, z_index] = np.minimum(
            full_mask[:, :, z_index],
            smooth_mask
        )

        return full_mask
    except Exception as e:
        print(f"Error en polígono suave: {e}")
        return full_mask


def restar_mask(full_mask, z_index):
    full_mask[:, :, z_index] = 1.0

    return full_mask
