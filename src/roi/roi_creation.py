import numpy as np


def create_rectangular_mask(roi_coords, full_mask, z_index):
    try:
        new_selection = np.zeros((full_mask.shape[0], full_mask.shape[1]), dtype=bool)

        x1, y1, x2, y2 = map(int, map(np.floor, roi_coords))
        ix1, ix2 = sorted([x1, x2])
        iy1, iy2 = sorted([y1, y2])

        ix1, ix2 = np.clip([ix1, ix2], 0, full_mask.shape[0])
        iy1, iy2 = np.clip([iy1, iy2], 0, full_mask.shape[1])

        new_selection[ix1:ix2, iy1:iy2] = True

        full_mask[:, :, z_index] = full_mask[:, :, z_index] & new_selection

        return full_mask

    except Exception as e:
        print(f"Error procesando el ROI: {e}")


def update_elliptical_mask_subtractive(full_mask, ellipsis_center, radius, z_index):
    try:
        xc, yc = ellipsis_center
        a, b = radius

        x = np.arange(full_mask.shape[0])
        y = np.arange(full_mask.shape[1])
        xv, yv = np.meshgrid(x, y, indexing='ij')

        inside_ellipse = ((xv - xc) ** 2 / a ** 2 + (yv - yc) ** 2 / b ** 2) <= 1

        full_mask[:, :, z_index] = full_mask[:, :, z_index] & inside_ellipse

        return full_mask

    except Exception as e:
        print(f"Error en máscara elíptica: {e}")
        return full_mask
