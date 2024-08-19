# --------------------------------------------------------------------------
# Software:     InVesalius - Software de Reconstrucao 3D de Imagens Medicas
# Copyright:    (C) 2001  Centro de Pesquisas Renato Archer
# Homepage:     http://www.softwarepublico.gov.br
# Contact:      invesalius@cti.gov.br
# License:      GNU - GPL 2 (LICENSE.txt/LICENCA.txt)
# --------------------------------------------------------------------------
#    Este programa e software livre; voce pode redistribui-lo e/ou
#    modifica-lo sob os termos da Licenca Publica Geral GNU, conforme
#    publicada pela Free Software Foundation; de acordo com a versao 2
#    da Licenca.
#
#    Este programa eh distribuido na expectativa de ser util, mas SEM
#    QUALQUER GARANTIA; sem mesmo a garantia implicita de
#    COMERCIALIZACAO ou de ADEQUACAO A QUALQUER PROPOSITO EM
#    PARTICULAR. Consulte a Licenca Publica Geral GNU para obter mais
#    detalhes.
# --------------------------------------------------------------------------

import numpy as np
from skimage.draw import polygon

import invesalius.constants as const
import invesalius.data.slice_ as slc
from invesalius.pubsub import pub as Publisher
from invesalius_cy.mask_cut import mask_cut, mask_cut_with_depth


class Mask3DEditException(Exception):
    pass


class Mask3DEditor:
    def __init__(self):
        self.__bind_events()
        self.polygons_to_operate = []
        self.spacing = None
        self.edit_mode = const.MASK_3D_EDIT_INCLUDE
        self.use_depth = False
        self.depth_val = None
        self.model_to_screen = None
        self.model_view = None
        self.resolution = None  # (w, h)
        self.clipping_range = None  # (near, far)

    def __bind_events(self):
        Publisher.subscribe(self.AddPolygon, "M3E add polygon")
        Publisher.subscribe(self.DoMaskEdit, "M3E apply edit")
        Publisher.subscribe(self.ClearPolygons, "M3E clear polygons")
        Publisher.subscribe(self.SetCamParameters, "M3E set camera")
        Publisher.subscribe(self.SetEditMode, "M3E set edit mode")
        Publisher.subscribe(self.SetUseDepthForEdit, "M3E use depth")
        Publisher.subscribe(self.SetDepthValue, "M3E depth value")

    def AddPolygon(self, points):
        """
        Adds polygon to be used in the edit
        """
        self.polygons_to_operate.append(points)

    def ClearPolygons(self):
        """
        Discards all added polygons
        """
        self.polygons_to_operate = []

    def SetCamParameters(self, params):
        """
        Sets the model-view-projection matrix used by the viewer
        """
        if "model_to_screen" in params:
            self.model_to_screen = params["model_to_screen"]
        if "model_view" in params:
            self.model_view = params["model_view"]
        if "resolution" in params:
            self.resolution = params["resolution"]
        if "clipping_range" in params:
            self.clipping_range = params["clipping_range"]

    def SetEditMode(self, mode):
        """
        Sets edit mode to either discard points within or outside
        the polygon.
        """
        self.edit_mode = mode

    def SetUseDepthForEdit(self, use):
        """
        Sets whether to perform a mask cut using depth or through all
        """
        self.use_depth = use

    def SetDepthValue(self, value):
        self.depth_val = value

    def __create_filter(self):
        """
        Based on the polygons and screen resolution,
        create a filter for the edit.
        """
        w, h = self.resolution
        _filter = np.zeros((h, w), dtype="uint8")

        # Include all selected polygons to create the cut
        for poly_points in self.polygons_to_operate:
            print(f"Poly Points: {poly_points}")
            poly = np.array(poly_points)
            rr, cc = polygon(poly[:, 1], poly[:, 0], _filter.shape)
            _filter[rr, cc] = 1

        if self.edit_mode == const.MASK_3D_EDIT_INCLUDE:
            _filter = 1 - _filter

        return _filter

    # Unoptimized implementation
    def __cut_mask(self, mask_data, spacing, _filter):
        """
        Cuts an Invesalius Mask with a filter (pixel-wise filter)
        mask_data: matrix data without metadata ([1:])
        spacing: the spacing used in the mask matrix
        _filter: matrix the same size as the viewer that rasterizes
        points to be edited
        """

        dz, dy, dx = mask_data.shape
        sx, sy, sz = spacing

        M = self.model_to_screen
        h, w = _filter.shape

        for z in range(dz):
            for y in range(dy):
                for x in range(dx):
                    # Voxel to world space
                    p0 = x * sx
                    p1 = y * sy
                    p2 = z * sz
                    p3 = 1.0

                    # _q = M * _p
                    _q0 = p0 * M[0, 0] + p1 * M[0, 1] + p2 * M[0, 2] + p3 * M[0, 3]
                    _q1 = p0 * M[1, 0] + p1 * M[1, 1] + p2 * M[1, 2] + p3 * M[1, 3]
                    _q2 = p0 * M[2, 0] + p1 * M[2, 1] + p2 * M[2, 2] + p3 * M[2, 3]
                    _q3 = p0 * M[3, 0] + p1 * M[3, 1] + p2 * M[3, 2] + p3 * M[3, 3]

                    if _q3 > 0:
                        q0 = _q0 / _q3
                        q1 = _q1 / _q3
                        q2 = _q2 / _q3

                        # Normalized coordinates back to pixels
                        px = (q0 / 2.0 + 0.5) * (w - 1)
                        py = (q1 / 2.0 + 0.5) * (h - 1)

                        if 0 <= px < w and 0 <= py < h:
                            if (
                                _filter[int(py), int(px)] == 1
                            ):  # NOTE: The lack of round here might be a problem
                                mask_data[z, y, x] = 0

    def DoMaskEdit(self):
        if len(self.polygons_to_operate) == 0:
            return

        s = slc.Slice()
        _cur_mask = s.current_mask

        if _cur_mask is None:
            raise Mask3DEditException("Attempted editing a non-existent mask")

        _filter = self.__create_filter()

        _prev_mat = _cur_mask.matrix.copy()

        # Unoptimized implementation
        # self.__cut_mask(_cur_mask.matrix[1:, 1:, 1:], s.spacing, _filter)

        # Optimized implementation
        _mat = _cur_mask.matrix[1:, 1:, 1:].copy()
        sx, sy, sz = s.spacing

        print(s.spacing)
        print(_mat.shape)

        if self.use_depth:
            near, far = self.clipping_range
            depth = near + (far - near) * self.depth_val
            mask_cut_with_depth(
                _mat, sx, sy, sz, depth, _filter, self.model_to_screen, self.model_view, _mat
            )
        else:
            mask_cut(_mat, sx, sy, sz, _filter, self.model_to_screen, _mat)

        _cur_mask.matrix[1:, 1:, 1:] = _mat
        _cur_mask.modified(all_volume=True)

        # Discard all buffers to reupdate view
        for ori in ["AXIAL", "CORONAL", "SAGITAL"]:
            s.buffer_slices[ori].discard_buffer()

        # Save modification in the history
        _cur_mask.save_history(0, "VOLUME", _cur_mask.matrix.copy(), _prev_mat)

        Publisher.sendMessage("Update mask 3D preview")
        Publisher.sendMessage("Reload actual slice")
