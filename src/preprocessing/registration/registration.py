import SimpleITK as sitk  # simpleitk library
import sys  # sys library, used to include local py files
import numpy as np  # array and matrix library
import matplotlib.pyplot as plt
import os
from nibabel.testing import data_path

import main
from src.utils.utils import start_register_plot, end_register_plot, update_multires_iterations, plot_register_values
from src.io.nfti_loader import load_nifti


def registration(data, affine, header):
    show_info(data)
    final_data = []
    fixed = data[:, :, :, 0].T
    fixed_image = sitk.GetImageFromArray(fixed)
    t_index = data.shape[3]
    spacing, origin, direction = get_sitk_metadata_from_nibabel(affine, header)

    fixed_image.SetSpacing(spacing)
    fixed_image.SetOrigin(origin)
    fixed_image.SetDirection(direction)

    final_data.append(sitk.GetArrayFromImage(fixed_image))
    for index in range(1, t_index):
        moving = data[:, :, :, index].T
        moving_image = sitk.GetImageFromArray(moving)

        moving_image.SetSpacing(spacing)
        moving_image.SetOrigin(origin)
        moving_image.SetDirection(direction)

        initial_transform = sitk.CenteredTransformInitializer(
            fixed_image,
            moving_image,
            sitk.Euler3DTransform(),
            sitk.CenteredTransformInitializerFilter.GEOMETRY
        )

        final_transform = registration_mi(fixed_image, moving_image, initial_transform, num_iterations=500,
                                          learning_rate=0.05, sampling=0.15)
        params = final_transform.GetParameters()
        print(f"Vol {index} -> Traslación: {params[3:]}")
        final_resampled = sitk.Resample(moving_image, fixed_image, final_transform,
                                        sitk.sitkLinear, 0.0, moving_image.GetPixelID())

        final_data.append(sitk.GetArrayFromImage(final_resampled))

    final_data_transform = np.stack(final_data)

    show_info(final_data_transform, True)

    check_overlay(data, final_data_transform)


def check_overlay(original_data, registered_data):
    # Seleccionamos el mismo corte en ambas
    # Nota: asumo que registered_data está en (T, Z, Y, X)
    t_idx = -1  # Comparamos con el último volumen del tiempo (donde suele haber más movimiento acumulado)
    slice_idx = registered_data.shape[1] // 2

    # Extraer los cortes
    fixed = registered_data[0, slice_idx, :, :]  # Referencia (T=0)
    moving = registered_data[t_idx, slice_idx, :, :]  # Registrada (T=final)

    plt.figure(figsize=(10, 5))

    # 1. Mostrar diferencia absoluta (donde hay blanco, hay error de alineación o realce)
    plt.subplot(1, 2, 1)
    diff = np.abs(fixed.astype(float) - moving.astype(float))
    plt.imshow(diff, cmap='hot')
    plt.title("Diferencia Absoluta\n(Bordes brillantes = Desalineación)")
    plt.colorbar()

    # 2. Superposición con Transparencia (Alpha Blend)
    plt.subplot(1, 2, 2)
    plt.imshow(fixed, cmap='gray')  # La fija de fondo en gris
    plt.imshow(moving, cmap='jet', alpha=0.3)  # La registrada encima en color y 30% opaca
    plt.title("Superposición (Overlay)\nFija (Gris) + Registrada (Color)")

    plt.tight_layout()
    plt.show()


def get_sitk_metadata_from_nibabel(affine, header):
    zooms = header.get_zooms()

    spacing = np.array(zooms[:3])

    print(spacing.shape)

    origin = affine[:3, 3].tolist()

    direction_matrix = affine[:3, :3] / spacing

    direction = direction_matrix.flatten().tolist()

    return spacing.tolist(), origin, direction


def registration_mi(fixed_image, moving_image, transform,
                    interpolator=sitk.sitkLinear,
                    bins=50, sampling=0.02,
                    num_iterations=50, learning_rate=1.5,
                    multiresolution=True, verbose=True, plot=True):
    '''
    Image regristration with metric mutual information (mi)
    Input:
        fixed_image: sitk.Image
        moving_image: sitk.Image
    Output:
        sitk.Transform
    '''
    # Define the registration object class
    registration_method = sitk.ImageRegistrationMethod()

    # Set transform, intepolation and metric
    registration_method.SetInitialTransform(transform)
    registration_method.SetInterpolator(interpolator)
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=bins)

    # Set the sampling method
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(sampling)

    # Set optimizer as gradient descent
    registration_method.SetOptimizerAsGradientDescent(learningRate=learning_rate,
                                                      numberOfIterations=num_iterations, convergenceMinimumValue=1e-6,
                                                      convergenceWindowSize=10)
    registration_method.SetOptimizerScalesFromPhysicalShift()  # Set appropiate scales

    # Setup for the multi-resolution framework.
    if multiresolution:
        registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
        registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
        registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    # Enable plotting
    if plot:
        registration_method.AddCommand(sitk.sitkStartEvent, start_register_plot)
        registration_method.AddCommand(sitk.sitkEndEvent, end_register_plot)
        if multiresolution: registration_method.AddCommand(sitk.sitkMultiResolutionIterationEvent,
                                                           update_multires_iterations)
        registration_method.AddCommand(sitk.sitkIterationEvent,
                                       lambda: plot_register_values(registration_method))

    transform_estimated = registration_method.Execute(fixed_image, moving_image)

    # Print the information about the optimization in the registration
    if verbose:
        info = '\n===== Registration Info ====='
        info += '\nFinal metric value: \t' + str(registration_method.GetMetricValue())
        info += '\nLast iteration: \t' + str(registration_method.GetOptimizerIteration())
        info += '\nStop condition: \n'
        info += (str(registration_method.GetOptimizerStopConditionDescription()))
        info += '\n'
        print(info)

    return transform_estimated


def show_info(data, is_processed=False):
    plt.figure(figsize=(6, 6))
    if is_processed:
        # data es (T, Z, Y, X)
        t_idx = 0
        slice_idx = data.shape[1] // 2
        img = data[t_idx, slice_idx, :, :]  # Ya está en orientación correcta para imshow
    else:
        # data es (X, Y, Z, T) de nibabel
        t_idx = 0
        slice_idx = data.shape[2] // 2
        img = data[:, :, slice_idx, t_idx].T

    plt.imshow(img, cmap='gray', origin='lower')
    plt.title(f'Corte axial: {slice_idx}')
    plt.axis('off')
    plt.show()


def main():
    example_file = os.path.join(data_path, 'example4d.nii.gz')
    data, affine, header = load_nifti(example_file)
    registration(data, affine, header)


if __name__ == "__main__":
    main()
