
import os
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import UID
import numpy as np
import imagecodecs

# HTJ2K Transfer Syntax UID (DICOM Standard)
HTJ2K_LOSSLESS = UID('1.2.840.10008.1.2.4.201')
HTJ2K_LOSSY = UID('1.2.840.10008.1.2.4.203')
JPEG2000_LOSSLESS = UID('1.2.840.10008.1.2.4.90')

class HTJ2KConverter:
    """
    DICOM to HTJ2K Converter using imagecodecs and pydicom.
    Falls back to JPEG 2000 Lossless if HTJ2K specific codec is unavailable.
    """
    
    @staticmethod
    def get_transfer_syntax(dataset: Dataset) -> UID:
        return dataset.file_meta.TransferSyntaxUID

    @staticmethod
    def is_htj2k(dataset: Dataset) -> bool:
        ts = HTJ2KConverter.get_transfer_syntax(dataset)
        return ts in [HTJ2K_LOSSLESS, HTJ2K_LOSSY]
        
    @staticmethod
    def convert_dataset(dataset: Dataset, lossless: bool = True) -> Dataset:
        """
        Convert a pydicom Dataset to HTJ2K transfer syntax.
        """
        # 1. Check if already HTJ2K
        if HTJ2KConverter.is_htj2k(dataset):
            return dataset
            
        # 2. Decompress pixel data if needed
        if dataset.file_meta.TransferSyntaxUID.is_compressed:
            dataset.decompress()
            
        # 3. Get pixel data as numpy array
        arr = dataset.pixel_array
        
        # 4. Encode using openjphpy or imagecodecs
        encoded_data = None
        target_uid = HTJ2K_LOSSLESS if lossless else HTJ2K_LOSSY
        
        try:
            # Try imagecodecs (if built with OpenJPH)
            if hasattr(imagecodecs, 'jph_encode'):
                encoded_data = imagecodecs.jph_encode(arr, lossless=lossless)
            else:
                # Try openjphpy
                try:
                    import openjphpy
                    # Assuming standard encode API if available, else fail to catch block
                    # Since openjphpy API documentation is scarce, we wrap safely.
                    # If this fails, we fall through to J2K fallback.
                    raise ImportError("openjphpy wrapper integration pending")
                except ImportError:
                     # Fallback to JPEG 2000 Lossless
                     # This preserves high compression losslessly but changes the Transfer Syntax UID.
                     # We MUST update the UID to reflect reality.
                     encoded_data = imagecodecs.jpeg2k_encode(arr, level=0 if lossless else 1)
                     target_uid = JPEG2000_LOSSLESS
        except Exception:
             # Final fallback to J2K if anything above explodes
             encoded_data = imagecodecs.jpeg2k_encode(arr, level=0 if lossless else 1)
             target_uid = JPEG2000_LOSSLESS

        # 5. Encapsulate for DICOM
        from pydicom.encaps import encapsulate
        compressed_pixel_data = encapsulate([encoded_data])
        
        # 6. Update Dataset
        dataset.PixelData = compressed_pixel_data
        dataset.file_meta.TransferSyntaxUID = target_uid
        dataset.is_implicit_VR = False
        dataset.is_little_endian = True
        
        # Update other tags
        if not lossless:
             dataset.LossyImageCompression = '01'
             dataset.LossyImageCompressionRatio = [10.0] # Dummy
             if target_uid == HTJ2K_LOSSLESS: 
                  target_uid = HTJ2K_LOSSY
                  dataset.file_meta.TransferSyntaxUID = target_uid

        return dataset

    @staticmethod
    def convert_file(file_path: str, output_path: str = None, lossless: bool = True) -> str:
        """
        Read file, convert, save. Returns new path.
        """
        ds = pydicom.dcmread(file_path)
        ds = HTJ2KConverter.convert_dataset(ds, lossless=lossless)
        
        if not output_path:
            base, ext = os.path.splitext(file_path)
            output_path = f"{base}_htj2k{ext}"
            
        ds.save_as(output_path)
        return output_path
