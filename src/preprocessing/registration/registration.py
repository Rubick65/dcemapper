import os

import SimpleITK as sitk  # simpleitk library
import matplotlib.pyplot as plt
import numpy as np  # array and matrix library
from nibabel.testing import data_path

from src.io.nifti_io import load_nifti
from src.utils.utils import start_register_plot, end_register_plot, update_multires_iterations, plot_register_values


def registration(data, affine, header):
    show_info(data)
    final_data = []
    fixed_data = data[:, :, :, 0].T

    origin = [float(o) for o in affine[:3, 3]]
    spacing = [float(s) for s in header.get_zooms()[:3]]
    direction = affine[:3, :3].flatten()

    fixed_image = sitk.GetImageFromArray(fixed_data)

    fixed_image.SetOrigin(origin)
    fixed_image.SetSpacing(spacing)
    fixed_image.SetDirection(direction)

    t_index = data.shape[3]

    final_data.append(sitk.GetArrayFromImage(fixed_image))
    for index in range(1, t_index):
        moving = data[:, :, :, index].T
        moving_image = sitk.GetImageFromArray(moving)

        moving_image.SetOrigin(origin)
        moving_image.SetDirection(direction)
        moving_image.SetSpacing(spacing)

        initial_transform = sitk.CenteredTransformInitializer(
            fixed_image,
            moving_image,
            sitk.Euler3DTransform(),
            sitk.CenteredTransformInitializerFilter.GEOMETRY
        )

        final_transform = registration_mi(fixed_image, moving_image, initial_transform, num_iterations=1000)
        params = final_transform.GetParameters()
        print(f"Vol {index} -> Traslación: {params[3:]}")
        final_resampled = sitk.Resample(moving_image, fixed_image, final_transform,
                                        sitk.sitkLinear, 0.0, moving_image.GetPixelID())

        final_data.append(sitk.GetArrayFromImage(final_resampled))

    final_data_transform = np.stack(final_data)

    show_info(final_data_transform, True)
    for s in range(final_data_transform.shape[1]):
        check_overlay(final_data_transform, slice_idx=s)


def check_overlay(registered_data, slice_idx=None):
    """
    Compara el volumen inicial con el final.
    Si slice_idx es None, usa el corte central por defecto.
    """
    # If slice index is none
    if slice_idx is None:
        slice_idx = registered_data.shape[1] // 2

    # Check that the index exists
    if slice_idx >= registered_data.shape[1]:
        return

    t_idx = -1
    fixed_slice = registered_data[0, slice_idx, :, :]
    moving_slice = registered_data[t_idx, slice_idx, :, :]

    plt.figure(figsize=(12, 5))

    # 1. Diferencia Absoluta
    plt.subplot(1, 2, 1)
    diff = np.abs(fixed_slice.astype(float) - moving_slice.astype(float))
    plt.imshow(diff, cmap='hot')
    plt.title(f"Diferencia Absoluta (Slice {slice_idx})\nBordes blancos = Desalineación")
    plt.colorbar()

    # 2. Superposición (Overlay)
    plt.subplot(1, 2, 2)
    plt.imshow(fixed_slice, cmap='gray')
    plt.imshow(moving_slice, cmap='jet', alpha=0.3)
    plt.title(f"Overlay (Slice {slice_idx})\nGris: Fijo | Color: Registrado")

    plt.tight_layout()
    plt.show()


def registration_mi(fixed_image, moving_image, transform,
                    interpolator=sitk.sitkLinear,
                    bins=60, sampling=0.10,
                    num_iterations=50, learning_rate=1.5,
                    multiresolution=True, verbose=True, plot=False):
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

    valor_inicial = registration_method.MetricEvaluate(fixed_image, moving_image)

    if valor_inicial <= -0.8:
        return None

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
                                                      convergenceWindowSize=30)
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

    print(valor_inicial)
    transform_estimated = registration_method.Execute(fixed_image, moving_image)

    valor_final = registration_method.GetMetricValue()
    print(f"Métrica final: {valor_final}")

    if valor_final > valor_inicial:
        print("¡Cuidado! El algoritmo ha empeorado la métrica. Es mejor no aplicar cambios.")

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
        img = data[t_idx, slice_idx, :, :]
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
