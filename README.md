<h1> Dcemapper </h1> 
Dcemapper is a Python desktop application designed for researchers and clinicians working with Dynamic Contrast Enhancement (DCE) MRI data. It provides an end-to-end workflow — from raw NIfTI file inspection to semi-quantitative parametric mapping — within an intuitive graphical interface.

## :hammer: Features
  - `📂 NIfTI loading`: Load and explore DCE-MRI volumes slice by slice and across time points:
    - `BIDS`: Auto-detects and loads NIfTI files from BIDS-compliant datasets.
    - `Single file`: Opens individual NIfTI files directly.
    - `Processed files`: Reloads previously processed outputs.
    - `Bruker conversion`: Converts raw Bruker data to NIfTI format.
    - 
  <img width="400" height="700" alt="image" src="https://github.com/user-attachments/assets/2583a4c7-6c35-4ddc-8ee1-278212739ada" /><br>
  <img width="300" height="200" alt="image" src="https://github.com/user-attachments/assets/0c81b8f0-8cb1-478d-aaeb-a914169cd5cc" />
    
  - `📈 Pixel intensity curves`: Click any voxel to show its signal intensity curve over the time.

    <img width="400" height="400" alt="image" src="https://github.com/user-attachments/assets/d102c01c-9036-461a-b5ff-9c97bc40f8aa" />

  - `🧹 Preprocessing`: Applies denoising and gibbs artifacts removal filters.
    
    <img width="692" height="158" alt="image" src="https://github.com/user-attachments/assets/581fc223-31c4-4fa1-a0a0-1fad287132cd" />

  - `🎯 ROI tools`: Draw regions of interest, save and reaload mask for reproducible analysis.
    
    <img width="394" height="234" alt="image" src="https://github.com/user-attachments/assets/66b3adf1-4118-4f61-907e-dd8a1d9fba0b" /><br>
    <img width="255" height="186" alt="image" src="https://github.com/user-attachments/assets/1105564d-9a56-49d2-9791-f373845a197c" />

 - `🗺️ Semi-quantitative mapping`: Generate three output NIfTI maps:  
    - `RCE`: Relative Contrast Enhancement.  
    - `RCEmax`: Maximum Relative Contrast Enhancement. 
    - `Time to RCE`: Time point of peak enhancement.

  <img width="390" height="127" alt="image" src="https://github.com/user-attachments/assets/07c9ab86-727a-4f76-a451-ad53a3f3eced" /><br>
  <img width="198" height="179" alt="image" src="https://github.com/user-attachments/assets/67872f97-5515-4086-98a0-632753a24669" />

  - `🎨 Customization`: Apply custom colormaps to enhance image contrast and perception.
   
    <img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/0aa709ec-229e-41c7-ab10-4529be32bae1" />

  - `🔍 Visualization`: Pan, zoom, and resize the image interactively for detailed inspection.

    <img width="408" height="77" alt="image" src="https://github.com/user-attachments/assets/648de4ff-94f0-412c-8d1d-7d547a3eeef2" />

  - `⌨️ Shortcuts`: Full keyboard shortcut support for every action.

    <img width="300" height="400" alt="image" src="https://github.com/user-attachments/assets/43835a35-b5a3-413b-b04a-2737aaf15804" />

  - `↔️ Layout`: Resizable panels to customize the workspace to your needs.

## Authors
<table border="0">
  <tr>
    <td align="center">
      <a href="https://github.com/Rubick65">
        <img src="https://github.com/Rubick65.png" width="150" style="border-radius:50%"/>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Hugodp22">
        <img src="https://github.com/Hugodp22.png" width="150" style="border-radius:50%"/>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center">
      <a href="https://github.com/Rubick65"><b>Rubén Martín Andrade</b></a>
    </td>
    <td align="center">
      <a href="https://github.com/Hugodp22"><b>Hugo de Pablo López</b></a>
    </td>
  </tr>
</table>


 
