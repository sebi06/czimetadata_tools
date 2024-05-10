from typing import Union, Optional
from dataclasses import dataclass, field
from box import Box
import os
from czitools.tools.logger import get_logger
from czitools.tools.box import get_czimd_box


logger = get_logger()

@dataclass
class CziMicroscope:
    czisource: Union[str, os.PathLike[str], Box]
    Id: Optional[str] = field(init=False)
    Name: Optional[str] = field(init=False)
    System: Optional[str] = field(init=False)

    def __post_init__(self):
        logger.info("Reading Microscope Information from CZI image data.")

        if isinstance(self.czisource, Box):
            czi_box = self.czisource
        else:
            czi_box = get_czimd_box(self.czisource)

        if czi_box.ImageDocument.Metadata.Information.Instrument is None:
            self.Id = None
            self.Name = None
            self.System = None
            logger.info("No Microscope information found.")

        else:
            self.Id = (
                czi_box.ImageDocument.Metadata.Information.Instrument.Microscopes.Microscope.Id
            )
            self.Name = (
                czi_box.ImageDocument.Metadata.Information.Instrument.Microscopes.Microscope.Name
            )
            self.System = (
                czi_box.ImageDocument.Metadata.Information.Instrument.Microscopes.Microscope.System
            )
