function ds_surf=remove_deep_vertices(fs_dir, ds_surf, orig_surf, ds_surf_fname, org_surf_fname)

vertices_to_keep=[];

mapping=knnsearch(orig_surf.vertices,ds_surf.vertices);
hemisphere_map=get_hemisphere_map(ds_surf_fname, org_surf_fname, 'recompute', true);
[lh_vertices, lh_label, lh_colortable] = read_annotation(fullfile(fs_dir,'label', 'lh.aparc.annot'));
[rh_vertices, rh_label, rh_colortable] = read_annotation(fullfile(fs_dir,'label', 'rh.aparc.annot'));

for i=1:size(ds_surf.vertices,1)
    orig_vtx=mapping(i);
    if hemisphere_map(i)==1
        if lh_label(orig_vtx)>0
            struct_idx=find(lh_colortable.table(:,5)==lh_label(orig_vtx));
            region=lh_colortable.struct_names{struct_idx};
            if ~strcmp(region,'unknown')
                vertices_to_keep(end+1)=i;
            end
        end
    else
        orig_vtx=orig_vtx-length(lh_vertices);
        if rh_label(orig_vtx)>0
            struct_idx=find(rh_colortable.table(:,5)==rh_label(orig_vtx));
            region=rh_colortable.struct_names{struct_idx};
            if ~strcmp(region,'unknown')
                vertices_to_keep(end+1)=i;
            end
        end
    end
end

% Create new array of vertices
new_vertices=ds_surf.vertices(vertices_to_keep,:);

% Find which faces to keep - ones that point to kept vertices
face_x=find(ismember(ds_surf.faces(:,1),vertices_to_keep));
face_y=find(ismember(ds_surf.faces(:,2),vertices_to_keep));
face_z=find(ismember(ds_surf.faces(:,3),vertices_to_keep));
faces_to_keep=intersect(intersect(face_x,face_y),face_z);

% Re-index faces
x_faces=reshape(ds_surf.faces(faces_to_keep,:),1,length(faces_to_keep)*3);
[y,idxs]=ismember(x_faces,vertices_to_keep);
new_faces=reshape(idxs,length(faces_to_keep),3);

% Create new surface
ds_surf.vertices=new_vertices;
ds_surf.faces=int32(new_faces);
if isfield(ds_surf,'normals')
    ds_surf.normals=ds_surf.normals(vertices_to_keep,:);
end


