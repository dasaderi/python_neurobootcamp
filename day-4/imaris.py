import os.path
import tables as tb
import re
import pandas as pd
import numpy as np
import trimesh

def read_table(table, index_col=None):
    df = pd.DataFrame(table.read())
    for column in df:
        if df[column].dtype == np.dtype('O'):
            df[column] = df[column].str.decode('utf')
    df.rename(columns=convert_camelcase, inplace=True)
    if index_col is not None:
        df.set_index(index_col, inplace=True, verify_integrity=True)
    return df


def convert_camelcase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return re.sub(r'(_+)', r'_', s2).lower()


def get_image_extents(fh):

    def extract_value(attrs, key):
        return float(''.join(attrs[key].astype('U')))

    image_attrs = fh.root.DataSetInfo.Image._v_attrs

    xlb = extract_value(image_attrs, 'ExtMin0')
    ylb = extract_value(image_attrs, 'ExtMin1')
    zlb = extract_value(image_attrs, 'ExtMin2')
    xub = extract_value(image_attrs, 'ExtMax0')
    yub = extract_value(image_attrs, 'ExtMax1')
    zub = extract_value(image_attrs, 'ExtMax2')
    x = extract_value(image_attrs, 'X')
    y = extract_value(image_attrs, 'Y')
    z = extract_value(image_attrs, 'Z')

    return {
        'x_start': xlb,
        'y_start': ylb,
        'z_start': zlb,
        'x_end': xub,
        'y_end': yub,
        'z_end': zub,
        'x_span': xub-xlb,
        'y_span': yub-ylb,
        'z_span': zub-zlb,
        'x_voxel': (xub-xlb)/x,
        'y_voxel': (yub-ylb)/y,
        'z_voxel': (zub-zlb)/z,
    }


def get_name(node):
    try:
        return node._v_attrs['Name'].astype('U')[0]
    except KeyError:
        return None


def find_scene_node(scene_node, name, ntype):
    for node in scene_node.Content._v_children.values():
        if ntype in node._v_name.lower():
            if get_name(node) == name:
                return node
    raise AttributeError('{} does not exist'.format(name))


def load_mesh(fh, name, color=None, split_by_surface=False):
    '''
    Loads mesh from scene
    '''
    node = find_scene_node(fh.root.Scene8, name, 'surface')
    vertices = read_table(node.Vertex)
    triangles = read_table(node.Triangle)
    vi = vertices[['position_x', 'position_y', 'position_z']].values
    vn = vertices[['normal_x', 'normal_y', 'normal_z']].values
    ti = triangles.values

    if split_by_surface:
        meshes = []
        surfaces = read_table(node.Surface)
        for _, surface in surfaces.iterrows():
            vlb = surface['index_vertex_begin']
            vub = surface['index_vertex_end']
            tlb = surface['index_triangle_begin']
            tub = surface['index_triangle_end']
            svi = vi[vlb:vub]
            svn = vn[vlb:vub]
            sti = ti[tlb:tub] - vlb
            mesh = trimesh.Trimesh(vertices=svi, faces=sti)
            mesh.surface_id = surface['id']
            if color is not None:
                mesh.visual.face_colors[:] = np.array(color)
            meshes.append(mesh)
        return meshes
    else:
        mesh = trimesh.Trimesh(vertices=vi, faces=ti, vertex_normals=vn)
        if color is not None:
            mesh.visual.face_colors[:] = np.array(color)
        return mesh


def load_node_stats(fh, name, ntype, xyz_base=None):
    '''
    Load statistics for scene node. This requires Imaris to have pre-computed
    them.
    '''
    node = find_scene_node(fh.root.Scene8, name, ntype)
    factor = read_table(node.Factor) \
            .query('name == "Channel"') \
            .set_index('id_list', verify_integrity=True)['level'].astype('int')
    factor.name = 'channel'

    creation = node._v_attrs['CreationParameters'].astype('U')[0]
    match = re.match(r'.*mSourceChannelIndex="(\d+)"', creation)
    channel = int(match.group(1)) + 1

    st = read_table(node.StatisticsType, 'id')
    sv = read_table(node.StatisticsValue) \
        .query('id_object >= 0') \
        .drop('id_time', axis=1) \
        .join(st, on='id_statistics_type') \
        .join(factor, on='id_factor_list') \
        .drop(['id_statistics_type', 'id_category', 'id_factor_list'], axis=1)

    to_drop = ['Time', 'Time Index', 'Distance to Image Border XY',
               'Distance to Image Border XYZ', 'Distance from Origin']
    sv.channel.fillna(channel, inplace=True)
    sv = sv.set_index(['name', 'channel', 'id_object'], verify_integrity=True)['value']
    sv = sv.xs(channel, level='channel').unstack('name').drop(to_drop, axis=1)

    if xyz_base is None:
        xyz_base = 'Position {}' if ntype == 'point' else 'Center of Image Mass {}'

    extents = get_image_extents(fh)
    for dim in 'XYZ':
        sv[dim] = sv[xyz_base.format(dim)]
        # Map data coordinates to pixel coordinates in image array
        origin = extents[dim.lower() + '_start']
        voxel_size = extents[dim.lower() + '_voxel']
        print(origin, voxel_size)
        data_coords = sv[dim]
        pixel_coords = (data_coords-origin)/voxel_size
        sv['index_' + dim] = pixel_coords.astype('i')
    return sv
