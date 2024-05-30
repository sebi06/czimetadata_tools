from typing import Union, List, Dict
from dataclasses import dataclass, field
from box import Box, BoxList
import os
import numpy as np
from collections import Counter
from czitools.utils import logging_tools
from czitools.utils.box import get_czimd_box
from czitools.utils.misc import get_planetable
from czitools.metadata_tools.dimension import CziDimensions

logger = logging_tools.set_logging()


@dataclass
class CziSampleInfo:
    czisource: Union[str, os.PathLike[str], Box]
    well_array_names: List[str] = field(init=False, default_factory=lambda: [])
    well_indices: List[int] = field(init=False, default_factory=lambda: [])
    well_position_names: List[str] = field(init=False, default_factory=lambda: [])
    well_colID: List[int] = field(init=False, default_factory=lambda: [])
    well_rowID: List[int] = field(init=False, default_factory=lambda: [])
    well_counter: Dict = field(init=False, default_factory=lambda: {})
    scene_stageX: List[float] = field(init=False, default_factory=lambda: [])
    scene_stageY: List[float] = field(init=False, default_factory=lambda: [])
    image_stageX: float = field(init=False, default=None)
    image_stageY: float = field(init=False, default=None)

    def __post_init__(self):
        logger.info("Reading SampleCarrier Information from CZI image data.")

        if isinstance(self.czisource, Box):
            czi_box = self.czisource
        else:
            czi_box = get_czimd_box(self.czisource)

        size_s = CziDimensions(czi_box).SizeS

        if size_s is not None:
            try:
                allscenes = (
                    czi_box.ImageDocument.Metadata.Information.Image.Dimensions.S.Scenes.Scene
                )

                if isinstance(allscenes, Box):
                    self.get_well_info(allscenes)

                if isinstance(allscenes, BoxList):
                    for well in range(len(allscenes)):
                        self.get_well_info(allscenes[well])

            except AttributeError:
                logger.info("CZI contains no scene metadata_tools.")

        elif size_s is None:
            logger.info(
                "No Scene or Well information found. Try to read XY Stage Coordinates from subblocks."
            )

            try:
                # read the data from CSV file
                planetable = get_planetable(
                    czi_box.filepath, pt_complete=False, t=0, c=0, z=0
                )

                self.image_stageX = float(planetable["X[micron]"][0])
                self.image_stageY = float(planetable["Y[micron]"][0])

            except Exception as e:
                logger.error(e)

    def get_well_info(self, well: Box):

        # check the ArrayName
        if well.ArrayName is not None:
            self.well_array_names.append(well.ArrayName)
            # count the well instances
            self.well_counter = Counter(self.well_array_names)

        if well.Index is not None:
            self.well_indices.append(int(well.Index))
        elif well.Index is None:
            logger.info("Well Index not found.")
            self.well_indices.append(1)

        if well.Name is not None:
            self.well_position_names.append(well.Name)
        elif well.Name is None:
            logger.info("Well Position Names not found.")
            self.well_position_names.append("P1")

        if well.Shape is not None:
            self.well_colID.append(int(well.Shape.ColumnIndex))
            self.well_rowID.append(int(well.Shape.RowIndex))
        elif well.Shape is None:
            logger.info("Well Column or Row IDs not found.")
            self.well_colID.append(0)
            self.well_rowID.append(0)

        if well.CenterPosition is not None:
            # get the SceneCenter Position
            sx = well.CenterPosition.split(",")[0]
            sy = well.CenterPosition.split(",")[1]
            self.scene_stageX.append(np.double(sx))
            self.scene_stageY.append(np.double(sy))
        elif well.CenterPosition is None:
            logger.info("Stage Positions XY not found.")
            self.scene_stageX.append(0.0)
            self.scene_stageY.append(0.0)
